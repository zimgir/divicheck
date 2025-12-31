#!/usr/bin/env python3

import sys

import argparse

from collections import defaultdict, OrderedDict
from statistics import mean
from pprint import pprint

import yfinance as yf
import pandas as pd
import numpy as np

from columns import *
from utils import *
from score import add_score_columns
from fetch import add_beta_column, update_eps_column
from filter import generate_thresholds, filter_with_thresholds



def add_sector_rank_and_sort(df):

    df["SectorRank"] = (
        df.groupby(COL_SECTOR)[COL_TOTAL_SCORE]
        .rank(method="dense", ascending=False)
    )

    df = df.sort_values(
        by=[COL_SECTOR, COL_SECTOR_RANK],
        na_position="last"
    ).reset_index(drop=True)


    return df

def preprocess_data(args, df):

    df = add_beta_column(df)

    df = update_eps_column(df)

    df = add_score_columns(df)

    df = add_sector_rank_and_sort(df)

    return df



def divicheck_preproc(args):

    print(f"\nLoad CSV data from {args.input}\n")

    src_data = csv_load_df(args.input)

    preproc_data = preprocess_data(args, src_data)

    generate_thresholds(args, preproc_data)

    csv_save_df(args.output, preproc_data)

    print(f"\nPreprocessed CSV written to {args.output}\n")



def divicheck_filter(args):

    print(f"\nLoad CSV data from {args.input}\n")

    src_data = csv_load_df(args.input)

    filtered_data = filter_with_thresholds(args, src_data)

    if len(filtered_data) == 0:
        print(f"\nNo data for output CSV after filtering :(\n")
        return

    csv_save_df(args.output, filtered_data)

    print(f"\nFiltered CSV written to {args.output}\n")



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Divident stocks CSV filter script using configurable JSON thresholds")

    subparsers = parser.add_subparsers(dest="action",required=True, help="Action to perform")

    preproc_parser = subparsers.add_parser("preproc", help="Preprocess source CSV data (add missing columns and cores) and Generate initial thresholds json")

    preproc_parser.add_argument("-i", "--input", required=True, help="Input path for all divident stocks CSV file from: https://www.dripinvesting.org")
    preproc_parser.add_argument("-o", "--output", default="_divident_stocks_data.csv", help="Output path for preprocessed divident stocks CSV file")
    preproc_parser.add_argument("-t", "--thresholds", default="_divident_stocks_thresholds.json", help="Output path for initial generated thresholds JSON for filtering")
    preproc_parser.add_argument("-w", "--weights", help="Optional score weights JSON to adjust score calulations during preprocessing")

    preproc_parser.set_defaults(func=divicheck_preproc)

    filter_parser = subparsers.add_parser("filter", help="Filter divident stock CSV file uisng input thresholds")

    preproc_parser.add_argument("-i", "--input", default="_divident_stocks_data.csv", help="Input path for preprocessed divident stocks CSV file")
    preproc_parser.add_argument("-o", "--output", default="_divident_stocks_filtered.csv", help="Output path for filtered divident stocks CSV file")
    preproc_parser.add_argument("-t", "--thresholds", default="_divident_stocks_thresholds.json", help="Input path for thresholds JSON which configures the filters")

    filter_parser.set_defaults(func=divicheck_filter)

    args = parser.parse_args()

    args.func(args)

