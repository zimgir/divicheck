
from collections import OrderedDict

# container for column definition data
class ColumnDefinition:
    def __init__(self, name, desc, unit=None, convert_factor=None, convert_factor_col=None):
        self.__dict__.update(locals())


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


# columns to delete from specific source data
COL_DELETE_SRC_DRIPINVESTING = {
    "Logo"
}

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
    "Debt/Capital",
    "P/E",
    "PEG",
    "P/BV"
}

COL_SAFETY_SCORE_INPUTS = {
    COL_ANNUAL_EPS,
    "Debt/Capital",
    "ROE",
    "CF/Share",
}
def column_normalize(
    df: pd.DataFrame,
    col: str,
    *,
    source_unit: str,
    target_unit: str | None = None,
    conversion_factor: float | None = None,
    fx_column: str | None = None,
    on_unexpected: str = "warn",  # "warn" | "error" | "ignore"
    metadata: dict | None = None,
) -> pd.DataFrame:
    """
    Explicit unit normalization with validation and metadata tracking.
    """

    s = df[col].astype(str)

    # --- Validate unexpected symbols ---
    allowed_symbols = set()
    if source_unit in UNIT_DEFINITIONS:
        allowed_symbols.update(UNIT_DEFINITIONS[source_unit]["symbols"])

    unexpected = (
        s.str.replace(r"[\d\.\-,\s]", "", regex=True)
         .str.replace("".join(allowed_symbols), "", regex=False)
    )

    if unexpected.str.len().gt(0).any():
        msg = f"Unexpected symbols in column '{col}'"
        if on_unexpected == "error":
            raise ValueError(msg)
        elif on_unexpected == "warn":
            print(f"WARNING: {msg}")

    # --- Remove known unit symbols ---
    for sym in allowed_symbols:
        s = s.str.replace(sym, "", regex=False)

    # --- Numeric cleanup ---
    values = (
        s.str.replace(",", "", regex=False)
         .str.replace(r"[^\d\.\-]", "", regex=True)
         .replace("", np.nan)
         .astype(float)
    )

    # --- Conversion logic ---
    if fx_column is not None:
        values = values * df[fx_column].astype(float)
    elif conversion_factor is not None:
        values = values * conversion_factor

    # --- Write back ---
    df[col] = values

    # --- Rename column ---
    final_unit = target_unit or source_unit
    suffix = UNIT_DEFINITIONS.get(final_unit, {}).get("suffix")

    if suffix:
        df = df.rename(columns={col: f"{col} ({suffix})"})

    # --- Metadata export ---
    if metadata is not None:
        metadata[col] = {
            "source_unit": source_unit,
            "target_unit": final_unit,
            "conversion_factor": conversion_factor,
            "fx_column": fx_column,
        }

    return df
