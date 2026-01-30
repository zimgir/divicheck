
import json
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

    for col_name in col_weights.keys():
        col_def = DVCSchema.get_col_def(col_name)

        if not col_def.is_numeric:
            raise Exception(f"Non numeric column {col_name} for score weights")

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


def compute_value_score(row):
    fv = to_float(row.get(COL_FAIR_VALUE_PCT))
    if fv is None:
        return 0.5

    # clamp to [-50%, +50%]
    fv = max(-50.0, min(50.0, fv))
    return (1.0 - (fv + 50.0) / 100.0)


def compute_safety_score(row, sector_stats):
    scores = []

    # Derived payout ratio proxy
    div = to_float(row.get(COL_ANNUAL_YIELD))
    eps = to_float(row.get(COL_ANNUAL_EPS))

    if div is not None and eps is not None and eps > 0:
        payout = div / eps
        scores.append(1.0 - min(payout, 1.5) / 1.5)
    else:
        payout = 0.0

    row[COL_PAYOUT_RATIO] = payout

    for col in COL_SAFETY_SCORE_INPUTS:
        v = to_float(row.get(col))
        if v is None:
            continue
        norm = sector_normalize(v, row[COL_SECTOR], sector_stats[col])
        if col in COL_LOWER_IS_BETTER:
            norm = 1.0 - norm
        scores.append(norm)

    return sum(scores) / len(scores) if scores else 0.5

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

            # normalize per row based on its sector
            norm = pd.Series(index=df.index, dtype=float)

            for sector, idx in df.groupby(SchemaColumns.SECTOR).groups.items():

                sector_stats = col_stats_per_sector[sector]

                norm.loc[idx] = normalize_to_sector(vals.loc[idx], sector_stats)

            # lower is better -> invert
            if col_def.lower_is_better:
                norm = 1.0 - norm

            mask = norm.notna()
            total.loc[mask] += norm[mask] * abs(w)
            wsum.loc[mask]  += abs(w)

        # valuation score for all rows at once
        value_score = compute_value_score(df)          # should return a Series
        total += value_score * value_weight
        wsum  += value_weight

        # safety score for all rows at once
        safety_score = compute_safety_score(df, safety_stats)  # should return a Series
        total += safety_score * safety_weight
        wsum  += safety_weight

        # write result columns to df
        df[SchemaColumns.VALUE_SCORE]  = value_score
        df[SchemaColumns.SAFETY_SCORE] = safety_score
        df[SchemaColumns.TOTAL_SCORE]  = total / wsum

        return df

    @staticmethod
    def add_score_columns(args, df):

        weights = load_weights(args)

        col_weights = weights.get(SCORE_WEIGHT_COLUMNS, {})
        value_weight = weights.get(SCORE_WEIGHT_VALUE, 0.0)
        safety_weight = weights.get(SCORE_WEIGHT_SAFETY, 0.0)

        sector_stats = {
            col: sector_min_max(df, col)
            for col in col_weights
        }

        safety_stats = {
            col: sector_min_max(df, col)
            for col in COL_SAFETY_SCORE_INPUTS
        }

        scored = []

        for row in rows:
            total = 0.0
            wsum = 0.0

            for col, w in col_weights.items():
                v = to_float(row.get(col))
                if v is None:
                    continue

                norm = sector_normalize(v, row[COL_SECTOR], sector_stats[col])

                if col in COL_LOWER_IS_BETTER:
                    norm = 1.0 - norm

                total += norm * abs(w)
                wsum += abs(w)

            # valuation bonus
            value_score = compute_value_score(row)
            total += value_score * value_weight
            wsum += value_weight

            row[COL_VALUE_SCORE] = value_score
            row.move_to_end(COL_VALUE_SCORE, last=False)

            # safety proxy
            safety_score = compute_safety_score(row, safety_stats)
            total += safety_score * safety_weight
            wsum += safety_weight

            row[COL_SAFETY_SCORE] = safety_score
            row.move_to_end(COL_SAFETY_SCORE, last=False)

            row[COL_TOTAL_SCORE] = total # / wsum if wsum else 0.0 # add this if want normalized score
            row.move_to_end(COL_TOTAL_SCORE, last=False)

            scored.append(row)

        return scored




