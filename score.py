
import json
import numpy as np
import pandas as pd


from schema import SchemaColumns, DVCSchema

SCORE_WEIGHT_COLUMNS = "columns"
SCORE_WEIGHT_SAFETY = "safety"
SCORE_WEIGHT_VALUE = "value"

# all weights are always positive and signify importance
# all columns are normalized according to sector to [0, 1] range
# lowe is better columns are inverted (1.0 - x) in the total score calculation
DEFAULT_SCORE_WEIGHTS = {
    SCORE_WEIGHT_COLUMNS: {
        SchemaColumns.YIELD_1Y: 1.2,
        SchemaColumns.CHOWDER: 1.5,
        SchemaColumns.DGR_5Y: 1.2,
        SchemaColumns.DGR_10Y: 1.0,
        SchemaColumns.EPS_1Y: 1.0,
        SchemaColumns.REVENUE_1Y: 0.8,
        SchemaColumns.ROE: 1.0,
        SchemaColumns.ROTC: 0.8,
        SchemaColumns.TTR_3Y: 1.0,
        SchemaColumns.DEBT_CAPITAL: 1.2,
        SchemaColumns.P_E: 0.8,
        SchemaColumns.PEG: 0.6,
    },

    # derrived scores
    SCORE_WEIGHT_SAFETY : 1.2,
    SCORE_WEIGHT_VALUE: 0.8,
}


def load_weights(args):
    if args.weights:
        with open(args.weights, "r") as f:
            weights = json.load(f)
    else:
        weights = DEFAULT_SCORE_WEIGHTS

    col_weights   = weights.get(SCORE_WEIGHT_COLUMNS, {})
    value_weight  = weights.get(SCORE_WEIGHT_VALUE, 0.0)
    safety_weight = weights.get(SCORE_WEIGHT_SAFETY, 0.0)

    for col_name, col_weight in col_weights.items():
        col_def = DVCSchema.get_col_def(col_name)

        if not col_def.is_numeric:
            raise Exception(f"Non numeric column {col_name} for score weights")

        col_weights[col_name] = abs(col_weight)

    value_weight = abs(value_weight)
    safety_weight = abs(safety_weight)

    return col_weights, value_weight, safety_weight


def calc_sector_stats(df, col_name):
    col_def = DVCSchema.get_col_def(col_name)

    if not col_def.is_numeric:
        raise Exception(f"Non numeric column {col_name} for sector min max")

    # Keep only rows with a valid numeric value in this column
    valid = df.dropna(subset=[col_name])

    # Group by sector and calculate min and max for the column
    grouped = valid.groupby(SchemaColumns.SECTOR)[col_name].agg(['min', 'max'])

    # Convert to {sector: (min, max)} like the original function
    return {
        sector: {"min": row['min'], "max": row['max']}
        for sector, row in grouped.iterrows()
    }


def get_col_sector_stats(df, col_name, stats_cache):

    if col_name in stats_cache:
        return stats_cache[col_name]

    col_stats_per_sector = calc_sector_stats(df, col_name)

    stats_cache[col_name] = col_stats_per_sector

    return col_stats_per_sector


def normalize_to_sector(val, sector_stats):

    sector_min = sector_stats["min"]
    sector_max = sector_stats["max"]

    denom = (sector_max - sector_min)
    if denom == 0:
        return 0.0
    else:
        norm_val = (val - sector_min) / denom
        return norm_val


def normalize_rows_to_sector(df, col_vals, col_stats_per_sector):

    # normalize per row based on its sector
    norm = pd.Series(index=df.index, dtype=float)

    for sector, idx in df.groupby(SchemaColumns.SECTOR).groups.items():

        sector_stats = col_stats_per_sector[sector]

        norm.loc[idx] = normalize_to_sector(col_vals.loc[idx], sector_stats)

    return norm


def compute_value_score(df, clip_min=50.0, clip_max=50.0):
    fv = df[SchemaColumns.FAIR_VALUE]

    # default score when fv is missing
    score = pd.Series(0.5, index=df.index)

    # clamp to [-50, 50]
    fv = fv.clip(lower=clip_min, upper=clip_max)

    # compute score where fv is valid
    mask = fv.notna()
    score[mask] = 1.0 - (fv[mask] + 50.0) / 100.0

    return score


def add_payout_column(df):
    df[SchemaColumns.PAYOUT_RATIO] = np.nan

    mask = (
        df[SchemaColumns.DIV_1Y].notna()
        & df[SchemaColumns.EPS_1Y].notna()
        & (df[SchemaColumns.EPS_1Y] > 0)
    )

    df.loc[mask, SchemaColumns.PAYOUT_RATIO] = df.loc[mask, SchemaColumns.DIV_1Y] / df.loc[mask, SchemaColumns.EPS_1Y]

    return df


def compute_safety_score(df, stats_cache):
    scores = []

    df = add_payout_column(df)

    safety_score_cols = {
        SchemaColumns.EPS_1Y,
        SchemaColumns.DEBT_CAPITAL,
        SchemaColumns.ROE,
        SchemaColumns.CF_SHARE,
        SchemaColumns.PAYOUT_RATIO
    }

    for col in safety_score_cols:

        col_def = DVCSchema.get_col_def(col)

        vals = df[col]

        col_stats_per_sector = get_col_sector_stats(df, col, stats_cache)

        norm = normalize_rows_to_sector(df, vals, col_stats_per_sector)

        # lower is better -> invert
        if col_def.lower_is_better:
            norm = 1.0 - norm

        scores.append(norm)

    total_safety_score = sum(scores) / len(scores)

    return total_safety_score



class DVCScore:

    @staticmethod
    def add_score_columns(args, df):
        col_weights, value_weight, safety_weight = load_weights(args)

        stats_cache = {}

        # accumulators as pandas Series
        total = pd.Series(0.0, index=df.index)
        wsum  = pd.Series(0.0, index=df.index)

        # main weighted columns
        for col, w in col_weights.items():

            col_def = DVCSchema.get_col_def(col)

            vals = df[col]

            col_stats_per_sector = get_col_sector_stats(df, col, stats_cache)

            norm = normalize_rows_to_sector(df, vals, col_stats_per_sector)

            # lower is better -> invert
            if col_def.lower_is_better:
                norm = 1.0 - norm

            mask = norm.notna()
            total.loc[mask] += norm[mask] * w
            wsum.loc[mask]  += w

        # valuation score for all rows at once
        value_score = compute_value_score(df)
        total += value_score * value_weight
        wsum  += value_weight

        # safety score for all rows at once
        safety_score = compute_safety_score(df, stats_cache)
        total += safety_score * safety_weight
        wsum  += safety_weight

        # write result columns to df
        df[SchemaColumns.VALUE_SCORE]  = value_score
        df[SchemaColumns.SAFETY_SCORE] = safety_score
        df[SchemaColumns.TOTAL_SCORE]  = total / wsum

        return df




