

from collections import OrderedDict

import numpy as np
import pandas as pd

from source import SRC_DEFS

# container for column definition data
class ColumnDefinition:
    def __init__(self, name, desc, unit=None):
        self.__dict__.update(locals())

        self.src_name = None


# main stock key
COL_SYMBOL = "Symbol"

# divicheck calculated scores
COL_SECTOR_RANK = "DVC Sector Rank"
COL_TOTAL_SCORE = "DVC Total Score"
COL_VALUE_SCORE = "DVC Value Score"
COL_SAFETY_SCORE = "DVC Safety Score"

# company info
COL_STOCK_TYPE = "Stock Type"
COL_COMPANY = "Company"
COL_SECTOR = "Sector"
COL_INDUSTRY = "Industry"

# main divident value info
COL_PRICE = "Price ($)"
COL_FAIR_VALUE = "FV P.L (%)"
COL_YIELD_1Y = "Yield 1Y (%)"
COL_YIELD_5Y = "Yield 5Y (%)"
COL_DIV_1Y = "Div 1Y ($)"
COL_CUR_DIV = "Cur Div ($)"
COL_NUM_DIV = "Num Div"
COL_PAY_DATE = "Pay Date"

# main divident sustainability info
COL_CHOWDER = "Chowder"
COL_ROE = "ROE (%)"
COL_PAYOUT_RATIO = "Payout Div/CF (%)"
COL_DEBT_CAPITAL = "Debt/Capital (%)"

# main divident growth info
COL_DGR_1Y = "DGR 1Y (%)"
COL_DGR_3Y = "DGR 3Y (%)"
COL_DGR_5Y = "DGR 5Y (%)"
COL_DGR_10Y = "DGR 10Y (%)"
COL_TTR_1Y = "TTR 1Y (%)"
COL_TTR_3Y = "TTR 3Y (%)"
COL_EPS_1Y = "EPS 1Y (%)"

# secondary evaluation parameters
COL_REVENUE_1Y = "Revenue 1Y (%)"
COL_NPM = "NPM (%)"
COL_ROTC = "ROTC (%)"
COL_CUR_R = "Cur R"
COL_P_E = "P/E (%)"
COL_P_BV = "P/BV (%)"
COL_CF_SHARE= "CF/Share ($)"
COL_PEG = "PEG"

# secondary divident info
COL_FAIR_PRICE = "FV P.L ($)"
COL_PRICE_LOW = "Low ($)"
COL_PRICE_HIGH = "High ($)"
COL_PREV_DIV = "Prev Div ($)"
COL_EX_DATE = "Ex Date"


# preprocessed column order schema
COL_DEFS = OrderedDict((
    # main stock key
    (COL_SYMBOL, ColumnDefinition(COL_SYMBOL, "Stock Symbol")),

    # divicheck calculated scores
    (COL_SECTOR_RANK, ColumnDefinition(COL_SECTOR_RANK, "Sector rank - lower is better overall in sector")),
    (COL_TOTAL_SCORE, ColumnDefinition(COL_TOTAL_SCORE, "Total score computed by divicheck - Higher is better overall")),
    (COL_VALUE_SCORE, ColumnDefinition(COL_VALUE_SCORE, "Value score computed by divicheck - Higher is better price to buy")),
    (COL_SAFETY_SCORE, ColumnDefinition(COL_SAFETY_SCORE, "Safety score computed by divicheck - Higher is better in terms of safety")),

    # company info
    (COL_STOCK_TYPE, ColumnDefinition(COL_STOCK_TYPE, "Divident stock type (in terms of increasing deividents) according to https://www.dripinvesting.org")),
    (COL_COMPANY, ColumnDefinition(COL_COMPANY, "Company name")),
    (COL_SECTOR, ColumnDefinition(COL_SECTOR, "Company sector")),
    (COL_INDUSTRY, ColumnDefinition(COL_INDUSTRY, "Company industry")),

    # main divident info
    (COL_PRICE, ColumnDefinition(COL_PRICE, "Current share price", unit="$")),
    (COL_FAIR_VALUE, ColumnDefinition(COL_FAIR_VALUE, "Percent over/under valued relative to fair value using Peter Lynch method", unit="%")),
    (COL_YIELD_1Y, ColumnDefinition(COL_YIELD_1Y, "Share yield % per year", unit="%")),
    (COL_YIELD_5Y, ColumnDefinition(COL_YIELD_5Y, "Share yield % per year on 5 years average", unit="$")),
    (COL_DIV_1Y, ColumnDefinition(COL_DIV_1Y, "Total divident yield over 1 year", unit="$")),
    (COL_CUR_DIV, ColumnDefinition(COL_CUR_DIV, "Most recent divident yield", unit="$")),
    (COL_NUM_DIV, ColumnDefinition(COL_NUM_DIV, "Number of divident payouts per year")),
    (COL_PAY_DATE, ColumnDefinition(COL_PAY_DATE, "Date of next divident payment", unit="date")),

    # main divident sustainability info
    (COL_CHOWDER, ColumnDefinition(COL_CHOWDER, "Dividend Yield + Dividend Growth Rate. Measures income + growth")),
    (COL_ROE, ColumnDefinition(COL_ROE, "Return on equity. Capital efficiency", unit="%")),
    (COL_PAYOUT_RATIO, ColumnDefinition(COL_PAYOUT_RATIO, "Anual divident to cashflow per share ratio, Lower is more sustainable", unit="%")),
    (COL_DEBT_CAPITAL, ColumnDefinition(COL_DEBT_CAPITAL, "Debt to total capital. Lower is safer", unit="%")),

    # main divident growth info
    (COL_DGR_1Y, ColumnDefinition(COL_DGR_1Y, "Dividend Growth Rate over 1 years", unit="%")),
    (COL_DGR_3Y, ColumnDefinition(COL_DGR_3Y, "Dividend Growth Rate over 3 years", unit="%")),
    (COL_DGR_5Y, ColumnDefinition(COL_DGR_5Y, "Dividend Growth Rate over 5 years", unit="%")),
    (COL_DGR_10Y, ColumnDefinition(COL_DGR_10Y, "Dividend Growth Rate over 10 years", unit="%")),
    (COL_TTR_1Y, ColumnDefinition(COL_TTR_1Y, "Total return over 1 year", unit="%")),
    (COL_TTR_3Y, ColumnDefinition(COL_TTR_3Y, "Total return over 3 years", unit="%")),
    (COL_EPS_1Y, ColumnDefinition(COL_EPS_1Y, "Earnings per share growth 1 year", unit="%")),

    # secondary evaluation parameters
    (COL_REVENUE_1Y, ColumnDefinition(COL_REVENUE_1Y, "Revenue growth over last year", unit="%")),
    (COL_NPM, ColumnDefinition(COL_NPM, "Net profit margin. Measures profitability", unit="%")),
    (COL_ROTC, ColumnDefinition(COL_ROTC, "Return on total capital", unit="%")),
    (COL_CUR_R, ColumnDefinition(COL_CUR_R, "Current ratio. Liquidity measure")),
    (COL_P_E, ColumnDefinition(COL_P_E, "Price-to-earnings ratio. Valuation metric", unit="%")),
    (COL_P_BV, ColumnDefinition(COL_P_BV, "Price-to-book value ratio", unit="%")),
    (COL_CF_SHARE, ColumnDefinition(COL_CF_SHARE, "Cash flow per share", unit="$")),
    (COL_PEG, ColumnDefinition(COL_PEG, "Price / Earnings to Growth ratio. Valuation adjusted for growth")),

    # secondary divident info
    (COL_FAIR_PRICE, ColumnDefinition(COL_FAIR_PRICE, "Fair price estimate using Peter Lynch method", unit="$")),
    (COL_PRICE_LOW, ColumnDefinition(COL_PRICE_LOW, "52-week low price", unit="$")),
    (COL_PRICE_HIGH, ColumnDefinition(COL_PRICE_HIGH, "52-week high price", unit="$")),
    (COL_PREV_DIV, ColumnDefinition(COL_PREV_DIV, "Previous divident yield", unit="$")),
    (COL_EX_DATE, ColumnDefinition(COL_EX_DATE, "???", unit="date")),

))


COL_LOWER_IS_BETTER = {
    COL_DEBT_CAPITAL,
    COL_P_BV,
    COL_P_E,
    COL_PEG,
}

COL_FILTER_TOTAL_SUM = {
    COL_DIV_1Y,
}


def schema_numeric_col_normalize(
    df: pd.DataFrame,
    src_cols,
    src_name,
    on_unexpected: str = "warn",  # "warn" | "error" | "ignore"
) -> pd.DataFrame:

    src_info = SRC_DEFS[src_name]

    # first delete all redundant cols according to src name
    cols_to_delete = src_info.get_delete_cols()

    if len(cols_to_delete) > 0:
        df = df.drop(cols_to_delete, axis=1)

    # normalize numeric columns for given source
    for src_col_name in src_cols:

        schema_col_name = src_info.get_col_schema_name(src_col_name)

        src_col_allowed_symbols = src_info.get_col_allowed_symbols(src_col_name)

        src_col_convert_col = src_info.get_col_convert_col_name(src_col_name)

        src_col_convert_factor = src_info.get_col_convert_factor(src_col_name)

        col_def = COL_DEFS[schema_col_name]

        # check for unexpected symbols
        s = df[src_col_name].astype(str)

        # remove always allowed numeric symbols
        unexpected = s.str.replace(r"[\d\.\-,\s]", "", regex=True)

        # remove col allowed symbols such as units like $
        for sym in src_col_allowed_symbols:
            unexpected = unexpected.str.replace(sym, "", regex=False)

        # check if anything unexpected left after removing all the expected
        if unexpected.str.len().gt(0).any():
            msg = f"Unexpected symbols in column '{src_col_name}' from source '{src_name}'"
            if on_unexpected == "error":
                raise ValueError(msg)
            elif on_unexpected == "warn":
                print(f"WARNING: {msg}")


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

        # rename column to schema name
        df = df.rename(columns={src_col_name: schema_col_name})

        # update metadata
        col_def.src_name = src_name

    return df
