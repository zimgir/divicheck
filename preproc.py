
from source import DVCSupportedDataSources

from utils import csv_load_df


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

def preprocess_data(data_path, data_source):

    #df = add_beta_column(df)

    #df = update_eps_column(df)

    #df = add_score_columns(df)

    #df = add_sector_rank_and_sort(df)

    return df


def preproc_dripinvesting(data_path):

    src_data = csv_load_df(data_path)

    #df = add_beta_column(df)

    #df = update_eps_column(df)

    #df = add_score_columns(df)

    #df = add_sector_rank_and_sort(df)

    return df


PREPROC_HANDLERS = {
    DVCSupportedDataSources.DRIPINVESTING : preproc_dripinvesting
}

class DVCPreprocess:

    @staticmethod
    def preprocess_data(args):

        if args.source not in PREPROC_HANDLERS:
            raise Exception(f"Unsupported preprocess data source: {args.source}")

        df = PREPROC_HANDLERS[args.source](args)

        return df


