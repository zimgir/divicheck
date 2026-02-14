#!/usr/bin/env python3

import os
import argparse


from utils import csv_save_df, json_save

from source import DVCSupportedDataSources
from preproc import DVCPreprocess
#from filter import DVCFilter
from schema import *



DEFAULT_PREPROC_SOURCE = DVCSupportedDataSources.DRIPINVESTING
DEFAULT_STOCKS_DATA = "_divident_stocks_data.csv"
DEFAULT_STOCKS_THRESHOLDS = "_divident_stocks_thresholds.json"
DEFAULT_STOCKS_FILTERED_DATA = "_divident_stocks_filtered.csv"



def divicheck_preproc(args):

    print(f"\n[PREPROC] Load data from {args.input} source: {args.source}\n")

    data = DVCPreprocess.preprocess_data(args)

    out_data_path = os.path.join(args.outdir, DEFAULT_STOCKS_DATA)

    csv_save_df(out_data_path, data)

    print(f"\n[PREPROC] Preprocessed data written to {out_data_path}\n")

    # thresholds = DVCFilter.generate_thresholds(args, data)

    # out_thresh_path = os.path.join(args.outdir, DEFAULT_STOCKS_THRESHOLDS)

    # json_save(out_thresh_path, thresholds)

    # print(f"\n[PREPROC] Preprocessed thresholds written to {out_thresh_path}\n")


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
    parser = argparse.ArgumentParser(description="Divident stocks filter script using configurable JSON thresholds")

    subparsers = parser.add_subparsers(dest="action",required=True, help="Action to perform")

    preproc_parser = subparsers.add_parser("preproc", help="Preprocess an existing stock data file from one of the supported sources into a common format and generate initial thresholds file for it")

    preproc_parser.add_argument("-i", "--input", required=True, help="Input path for divident stocks data file")
    preproc_parser.add_argument("-o", "--outdir", default=os.getcwd(), help="Output directory for preprocess outputs")
    preproc_parser.add_argument("-s", "--source", default=DEFAULT_PREPROC_SOURCE, help="Source of the input data for preprocessing")
    preproc_parser.add_argument("-w", "--weights", help="Optional score weights file to adjust score calulations during preprocessing")
    preproc_parser.add_argument("--dump-weights", action="store_true", help="Dump the used score weight file")

    preproc_parser.set_defaults(func=divicheck_preproc)

    filter_parser = subparsers.add_parser("filter", help="Filter divident stock CSV file uisng input thresholds")

    filter_parser.add_argument("-i", "--input", default=DEFAULT_STOCKS_DATA, help="Input path for preprocessed divident stocks CSV file")
    filter_parser.add_argument("-o", "--output", default=DEFAULT_STOCKS_FILTERED_DATA, help="Output path for filtered divident stocks CSV file")
    filter_parser.add_argument("-t", "--thresholds", default=DEFAULT_STOCKS_THRESHOLDS, help="Input path for thresholds JSON which configures the filters")

    filter_parser.set_defaults(func=divicheck_filter)

    args = parser.parse_args()

    args.func(args)

