import json
import pandas as pd
from pprint import pprint
from collections import OrderedDict

from utils import csv_load_df
from schema import DVCSchema, SchemaColumns


class DVCFilterKeys:
    NAME = "name"
    FILTER_ONLY = "filter_only"
    FILTER_DROP = "filter_drop"
    FILTER_MIN = "filter_min"
    FILTER_MAX = "filter_max"
    STAT_MIN = "stat_min"
    STAT_MAX = "stat_max"
    STAT_AVG = "stat_avg"
    DESC = "desc"


def load_filters(args):

    with open(args.filters, "r") as f:
        filters = json.load(f)

    return filters


def update_filter_stats(filter_stats, col_name, filter_name, filter_count):
    if filter_stats is None:
        return

    filter_stats_name = f"{col_name}_{filter_name}"
    filter_total_count = filter_stats.get(filter_stats_name, 0)
    filter_total_count += int(filter_count)
    filter_stats[filter_stats_name] = filter_total_count


def print_filter_stats(filter_stats):
    if filter_stats is None:
        return

    print("\n[FILTER] stats:\n")

    filter_stats = OrderedDict(sorted(filter_stats.items(),key=lambda x: x[1], reverse=True))

    pprint(filter_stats)


def add_summary_rows(df, round_digits=2, label_col=SchemaColumns.SYMBOL, separator="-----"):
    if df.empty:
        return df

    # Identify numeric columns
    numeric_cols = df.select_dtypes(include="number").columns

    # Final mask: numeric AND marked
    sum_cols = [col for col in numeric_cols if DVCSchema.get_col_def(col).calc_sum]

    # Aggregations
    agg_dict = {
        col: ["min", "max", "mean"] for col in numeric_cols
    }

    # Add sum only for selected columns
    for col in sum_cols:
        agg_dict[col].append("sum")

    agg_df = df.agg(agg_dict)

    # Rename mean -> avg
    agg_df = agg_df.rename(index={"mean": "avg"})

    # Optional rounding (presentation only)
    if round_digits is not None:
        agg_df = agg_df.round(round_digits)

    # Reindex to full column set
    agg_df = agg_df.reindex(columns=df.columns, fill_value="")

    # Put summary labels inside chosen column
    agg_df[label_col] = agg_df.index

    # Reset index to avoid duplicate index labels
    agg_df = agg_df.reset_index(drop=True)

    # Create separator row
    separator_row = {col : separator for col in df.columns}

    separator_df = pd.DataFrame([separator_row])

    # Combine everything
    final_df = pd.concat(
        [agg_df, separator_df, df],
        ignore_index=True
    )

    return final_df


class DVCFilter:

    @staticmethod
    def filter_data(args, keep_na=True, summary_rows=True):

        df = csv_load_df(args.input)

        filters = load_filters(args)

        mask = pd.Series(True, index=df.index)

        filter_stats = OrderedDict()

        num_rows_before = mask.sum()

        print(f"\n[FILTER] Got {num_rows_before} rows before filtering\n")

        for filter in filters:

            num_rows_before = mask.sum()

            # if there are no more rows to filter - stop
            if num_rows_before == 0:
                break

            col = filter.get(DVCFilterKeys.NAME, None)

            if col is None:
                continue

            if col not in df.columns:
                continue

            col_def = DVCSchema.get_col_def(col)

            col_series = df[col]
            col_is_numeric = col_def.is_numeric

            # ----------------------------
            # Numeric filters
            # ----------------------------
            if col_is_numeric:

                filter_min = filter.get(DVCFilterKeys.FILTER_MIN, None)

                if filter_min is not None:
                    num_rows_before = mask.sum()

                    if keep_na:
                        mask &= col_series >= filter_min | col_series.isna()
                    else:
                        mask &= col_series >= filter_min

                    filter_count = num_rows_before - mask.sum()

                    update_filter_stats(filter_stats, col, DVCFilterKeys.FILTER_MIN, filter_count)


                filter_max = filter.get(DVCFilterKeys.FILTER_MAX, None)

                if filter_max is not None:
                    num_rows_before = mask.sum()

                    if keep_na:
                        mask &= col_series <= filter_max | col_series.isna()
                    else:
                        mask &= col_series <= filter_max

                    filter_count = num_rows_before - mask.sum()

                    update_filter_stats(filter_stats, col, DVCFilterKeys.FILTER_MAX, filter_count)

            # ----------------------------
            # Categorical filters
            # ----------------------------
            else:

                filter_only = filter.get(DVCFilterKeys.FILTER_ONLY, ())

                if len(filter_only) > 0:
                    allowed = set(filter_only)

                    num_rows_before = mask.sum()

                    mask &= col_series.isin(allowed)

                    filter_count = num_rows_before - mask.sum()

                    update_filter_stats(filter_stats, col, DVCFilterKeys.FILTER_ONLY, filter_count)


                filter_drop = filter.get(DVCFilterKeys.FILTER_DROP, ())

                if len(filter_only) > 0:

                    excluded = set(filter_drop)

                    num_rows_before = mask.sum()

                    mask &= ~col_series.isin(excluded)

                    filter_count = num_rows_before - mask.sum()

                    update_filter_stats(filter_stats, col, DVCFilterKeys.FILTER_DROP, filter_count)


        print_filter_stats(filter_stats)

        print(f"\n[FILTER] Got {mask.sum()} rows after filtering\n")

        if df.empty:
            return df

        if summary_rows:
            filtered_df = add_summary_rows(df[mask])
        else:
            filtered_df = df[mask]

        return filtered_df

    @staticmethod
    def generate_filters(args, df):

        filters = []

        for col in df.columns:

            col_def = DVCSchema.get_col_def(col)

            col_filter = OrderedDict()

            col_filter[DVCFilterKeys.NAME] = col
            col_filter[DVCFilterKeys.FILTER_ONLY] = []
            col_filter[DVCFilterKeys.FILTER_DROP] = []

            if col_def.is_numeric:

                col_series = df[col]

                col_filter[DVCFilterKeys.FILTER_MIN] = None
                col_filter[DVCFilterKeys.FILTER_MAX] = None

                col_filter[DVCFilterKeys.STAT_MIN] = col_series.min(skipna=True)
                col_filter[DVCFilterKeys.STAT_MAX] = col_series.max(skipna=True)
                col_filter[DVCFilterKeys.STAT_AVG] = col_series.mean(skipna=True)


            col_filter[DVCFilterKeys.DESC] = col_def.desc

            filters.append(col_filter)


        return filters
