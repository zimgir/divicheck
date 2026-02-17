

from collections import OrderedDict

import numpy as np
import pandas as pd


# container for column definition data
class ColumnDefinition:
    def __init__(self, name, desc, unit=None, is_numeric=True, lower_is_better=False, calc_avg=True, calc_sum=False):
        self.__dict__.update(locals())

        self.src_info = None

class SchemaColumns:

    # main stock key
    SYMBOL = "Symbol"

    # divicheck calculated scores
    SECTOR_RANK = "DVC Sector Rank"
    TOTAL_SCORE = "DVC Total Score"
    VALUE_SCORE = "DVC Value Score"
    SAFETY_SCORE = "DVC Safety Score"

    # company info
    STOCK_TYPE = "Stock Type"
    COMPANY = "Company"
    SECTOR = "Sector"
    INDUSTRY = "Industry"

    # main divident value info
    PRICE = "Price ($)"
    FAIR_VALUE = "FV P.L (%)"
    YIELD_1Y = "Yield 1Y (%)"
    YIELD_5Y = "Yield 5Y (%)"
    DIV_1Y = "Div 1Y ($)"
    CUR_DIV = "Cur Div ($)"
    NUM_DIV_1Y = "Num Div 1Y"
    PAY_DATE = "Pay Date"

    # main divident sustainability info
    CHOWDER = "Chowder"
    ROE = "ROE (%)"
    PAYOUT_RATIO = "Payout Div/EPS (%)"
    DEBT_CAPITAL = "Debt/Capital (%)"

    # main divident growth info
    DGR_1Y = "DGR 1Y (%)"
    DGR_3Y = "DGR 3Y (%)"
    DGR_5Y = "DGR 5Y (%)"
    DGR_10Y = "DGR 10Y (%)"
    TTR_1Y = "TTR 1Y (%)"
    TTR_3Y = "TTR 3Y (%)"
    EPS_1Y = "EPS 1Y (%)"

    # secondary evaluation parameters
    REVENUE_1Y = "Revenue 1Y (%)"
    NPM = "NPM (%)"
    ROTC = "ROTC (%)"
    CUR_R = "Cur R"
    P_E = "P/E (%)"
    P_BV = "P/BV (%)"
    CF_SHARE= "CF/Share ($)"
    PEG = "PEG"

    # secondary divident info
    FAIR_PRICE = "FV P.L ($)"
    PRICE_LOW = "Low ($)"
    PRICE_HIGH = "High ($)"
    PREV_DIV = "Prev Div ($)"
    EX_DATE = "Ex Date"


# preprocessed column order schema
COL_DEFS = OrderedDict((
    # main stock key
    (SchemaColumns.SYMBOL, ColumnDefinition(SchemaColumns.SYMBOL, "Stock Symbol", is_numeric=False)),

    # divicheck calculated scores
    (SchemaColumns.SECTOR_RANK, ColumnDefinition(SchemaColumns.SECTOR_RANK,
                                                  "Sector rank - lower is better overall in sector")),
    (SchemaColumns.TOTAL_SCORE, ColumnDefinition(SchemaColumns.TOTAL_SCORE,
                                                  "Total score computed by divicheck - Higher is better overall")),
    (SchemaColumns.VALUE_SCORE, ColumnDefinition(SchemaColumns.VALUE_SCORE,
                                                  "Value score computed by divicheck - Higher is better price to buy")),
    (SchemaColumns.SAFETY_SCORE, ColumnDefinition(SchemaColumns.SAFETY_SCORE,
                                                   "Safety score computed by divicheck - Higher is better in terms of safety")),

    # company info
    (SchemaColumns.STOCK_TYPE, ColumnDefinition(SchemaColumns.STOCK_TYPE,
                                                "Divident stock type (in terms of increasing deividents) according to https://www.dripinvesting.org",
                                                is_numeric=False)),
    (SchemaColumns.COMPANY, ColumnDefinition(SchemaColumns.COMPANY, "Company name", is_numeric=False)),
    (SchemaColumns.SECTOR, ColumnDefinition(SchemaColumns.SECTOR, "Company sector", is_numeric=False)),
    (SchemaColumns.INDUSTRY, ColumnDefinition(SchemaColumns.INDUSTRY, "Company industry", is_numeric=False)),

    # main divident info
    (SchemaColumns.YIELD_1Y, ColumnDefinition(SchemaColumns.YIELD_1Y,
                                               "Share divident yield % per year", unit="%")),
    (SchemaColumns.YIELD_5Y, ColumnDefinition(SchemaColumns.YIELD_5Y,
                                               "Share yield % per year on 5 years average", unit="$")),

    (SchemaColumns.DIV_1Y, ColumnDefinition(SchemaColumns.DIV_1Y,
                                             "Total divident yield over 1 year", unit="$", calc_sum=True)),
    (SchemaColumns.PRICE, ColumnDefinition(SchemaColumns.PRICE,
                                            "Current share price", unit="$")),
    (SchemaColumns.FAIR_VALUE, ColumnDefinition(SchemaColumns.FAIR_VALUE,
                                                 "Percent over/under valued relative to fair value using Peter Lynch method", unit="%", lower_is_better=True)),


    (SchemaColumns.CUR_DIV, ColumnDefinition(SchemaColumns.CUR_DIV,
                                              "Most recent divident yield", unit="$")),
    (SchemaColumns.NUM_DIV_1Y, ColumnDefinition(SchemaColumns.NUM_DIV_1Y,
                                                 "Number of divident payouts per year")),
    (SchemaColumns.PAY_DATE, ColumnDefinition(SchemaColumns.PAY_DATE,
                                               "Date of next divident payment", unit="date", is_numeric=False)),

    # main divident sustainability info
    (SchemaColumns.CHOWDER, ColumnDefinition(SchemaColumns.CHOWDER,
                                              "Dividend Yield + Dividend Growth Rate. Measures income + growth")),
    (SchemaColumns.ROE, ColumnDefinition(SchemaColumns.ROE,
                                          "Return on equity. Capital efficiency", unit="%")),
    (SchemaColumns.PAYOUT_RATIO, ColumnDefinition(SchemaColumns.PAYOUT_RATIO,
                                                   "Anual divident to cashflow per share ratio, Lower is more sustainable", unit="%", lower_is_better=True)),
    (SchemaColumns.DEBT_CAPITAL, ColumnDefinition(SchemaColumns.DEBT_CAPITAL,
                                                   "Debt to total capital. Lower is safer", unit="%", lower_is_better=True)),

    # main divident growth info
    (SchemaColumns.DGR_1Y, ColumnDefinition(SchemaColumns.DGR_1Y,
                                             "Dividend Growth Rate over 1 years", unit="%")),
    (SchemaColumns.DGR_3Y, ColumnDefinition(SchemaColumns.DGR_3Y,
                                             "Dividend Growth Rate over 3 years", unit="%")),
    (SchemaColumns.DGR_5Y, ColumnDefinition(SchemaColumns.DGR_5Y,
                                             "Dividend Growth Rate over 5 years", unit="%")),
    (SchemaColumns.DGR_10Y, ColumnDefinition(SchemaColumns.DGR_10Y,
                                              "Dividend Growth Rate over 10 years", unit="%")),
    (SchemaColumns.TTR_1Y, ColumnDefinition(SchemaColumns.TTR_1Y,
                                             "Total return over 1 year", unit="%")),
    (SchemaColumns.TTR_3Y, ColumnDefinition(SchemaColumns.TTR_3Y,
                                             "Total return over 3 years", unit="%")),
    (SchemaColumns.EPS_1Y, ColumnDefinition(SchemaColumns.EPS_1Y,
                                             "Earnings per share growth 1 year", unit="%")),

    # secondary evaluation parameters
    (SchemaColumns.REVENUE_1Y, ColumnDefinition(SchemaColumns.REVENUE_1Y,
                                                 "Revenue growth over last year", unit="%")),
    (SchemaColumns.NPM, ColumnDefinition(SchemaColumns.NPM,
                                          "Net profit margin. Measures profitability", unit="%")),
    (SchemaColumns.ROTC, ColumnDefinition(SchemaColumns.ROTC,
                                           "Return on total capital", unit="%")),
    (SchemaColumns.CUR_R, ColumnDefinition(SchemaColumns.CUR_R,
                                            "Current ratio. Liquidity measure")),
    (SchemaColumns.P_E, ColumnDefinition(SchemaColumns.P_E,
                                          "Price-to-earnings ratio. Valuation metric", unit="%", lower_is_better=True)),
    (SchemaColumns.P_BV, ColumnDefinition(SchemaColumns.P_BV,
                                           "Price-to-book value ratio", unit="%", lower_is_better=True)),
    (SchemaColumns.CF_SHARE, ColumnDefinition(SchemaColumns.CF_SHARE,
                                               "Cash flow per share", unit="$")),
    (SchemaColumns.PEG, ColumnDefinition(SchemaColumns.PEG,
                                          "Price / Earnings to Growth ratio. Valuation adjusted for growth", lower_is_better=True)),

    # secondary divident info
    (SchemaColumns.FAIR_PRICE, ColumnDefinition(SchemaColumns.FAIR_PRICE,
                                                 "Fair price estimate using Peter Lynch method", unit="$")),
    (SchemaColumns.PRICE_LOW, ColumnDefinition(SchemaColumns.PRICE_LOW,
                                                "52-week low price", unit="$")),
    (SchemaColumns.PRICE_HIGH, ColumnDefinition(SchemaColumns.PRICE_HIGH,
                                                "52-week high price", unit="$")),
    (SchemaColumns.PREV_DIV, ColumnDefinition(SchemaColumns.PREV_DIV,
                                               "Previous divident yield", unit="$")),
    (SchemaColumns.EX_DATE, ColumnDefinition(SchemaColumns.EX_DATE,
                                             "???", unit="date", is_numeric=False)),

))

class DVCSchema:

    @staticmethod
    def get_col_order():
        return COL_DEFS.keys()

    @staticmethod
    def get_col_def(col_name):

        if col_name not in COL_DEFS:
            raise Exception(f"Col name: {col_name} is not in schema")

        return COL_DEFS[col_name]

    @staticmethod
    def normalize_numeric_col(df, src_info, src_col_name, on_unexpected="warn"):

        src_col_allowed_symbols = src_info.get_col_allowed_symbols(src_col_name)

        src_col_convert_col = src_info.get_col_convert_col_name(src_col_name)

        src_col_convert_factor = src_info.get_col_convert_factor(src_col_name)

        # check for unexpected symbols
        s = df[src_col_name].astype(str)

        # remove always allowed numeric symbols
        unexpected = s.str.replace(r"[\d\.\-,\s]", "", regex=True)

        # remove col allowed symbols such as units like $
        for sym in src_col_allowed_symbols:
            unexpected = unexpected.str.replace(sym, "", regex=False)

        # check if anything unexpected left after removing all the expected
        found_unexpected = unexpected.str.len().gt(0)

        if found_unexpected.any():
            unexpected = unexpected[found_unexpected]
            msg = f"Unexpected symbols\n'{unexpected}'\nin column '{src_col_name}' from source '{src_info.get_name()}'"

            if on_unexpected == "error":
                raise ValueError(msg)
            elif on_unexpected == "warn":
                print(f"\nWARNING: {msg}\n")


        # remove expected non numeric symbols such as units
        for sym in src_col_allowed_symbols:
            s = s.str.replace(sym, "", regex=False)

        # remove all non numeric symbols - empty col turns into a NaN - as float
        values = (
            s.str.replace(r"[^\d\.\-]", "", regex=True)
            .replace("", np.nan)
            .astype(float)
        )

        # conversion logic for curency or %
        if src_col_convert_col is not None:
            values = values * df[src_col_convert_col].astype(float)
        elif src_col_convert_factor is not None:
            values = values * src_col_convert_factor

        # write back normalized data
        df[src_col_name] = values


    @staticmethod
    def normalize_cols(df, src_info):

        # first delete all redundant cols according to src info
        cols_to_delete = src_info.get_delete_cols()

        if len(cols_to_delete) > 0:
            df = df.drop(cols_to_delete, axis=1)

        # normalize all columns for given source
        for src_col_name, schema_col_name in src_info.get_col_names():

            col_def = DVCSchema.get_col_def(schema_col_name)

            if col_def.is_numeric:
                DVCSchema.normalize_numeric_col(df, src_info, src_col_name)

            # rename src column to schema name
            df = df.rename(columns={src_col_name: schema_col_name})

            # update source metadata
            col_def.src_info = src_info

        return df
