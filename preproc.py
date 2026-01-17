import os

from source import DVCSupportedDataSources

from utils import csv_load_df
from source import DVCSource
from schema import DVCSchema


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



def preproc_dripinvesting(args, src_info):

    df = csv_load_df(args.input)

    df = DVCSchema.normalize_cols(df, src_info)

    #df = add_beta_column(df) #TODO

    #df = update_eps_column(df) #TODO

    df = add_score_columns(df)

    df = add_sector_rank_and_sort(df)

    return df


PREPROC_HANDLERS = {
    DVCSupportedDataSources.DRIPINVESTING : preproc_dripinvesting
}

class DVCPreprocess:

    @staticmethod
    def preprocess_data(args):

        if args.source not in PREPROC_HANDLERS:
            raise Exception(f"Unsupported preprocess data source: {args.source}")

        src_info = DVCSource.get_source(args.source)

        df = PREPROC_HANDLERS[args.source](args, src_info)

        return df


