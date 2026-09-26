from dataclasses import dataclass

@dataclass
class DBColumn:
    name: str
    data_type: str
    is_pk: bool = False
    indexed: bool = False
    extra_sql: str = ""

SCHEMA = {
    "SYMBOL": DBColumn("SYMBOL", "TEXT", is_pk=True),
    "SECTOR": DBColumn("SECTOR", "TEXT", indexed=True),
    "PRICE": DBColumn("PRICE", "REAL"),
    "FAIR_VALUE": DBColumn("FAIR_VALUE", "REAL"),
    "YIELD_1Y": DBColumn("YIELD_1Y", "REAL", indexed=True),
    "YIELD_5Y": DBColumn("YIELD_5Y", "REAL"),
    "TTR_1Y": DBColumn("TTR_1Y", "REAL"),
    "TTR_3Y": DBColumn("TTR_3Y", "REAL"),
    "DGR_1Y": DBColumn("DGR_1Y", "REAL"),
    "DGR_3Y": DBColumn("DGR_3Y", "REAL"),
    "DGR_5Y": DBColumn("DGR_5Y", "REAL", indexed=True),
    "DGR_10Y": DBColumn("DGR_10Y", "REAL"),
    "CHOWDER": DBColumn("CHOWDER", "REAL"),
    "ROE": DBColumn("ROE", "REAL"),
    "NPM": DBColumn("NPM", "REAL"),
    "ROTC": DBColumn("ROTC", "REAL"),
    "CUR_R": DBColumn("CUR_R", "REAL"),
    "EPS_1Y": DBColumn("EPS_1Y", "REAL"),
    "CF_SHARE": DBColumn("CF_SHARE", "REAL"),
    "PAYOUT_RATIO": DBColumn("PAYOUT_RATIO", "REAL"),
    "DEBT_CAPITAL": DBColumn("DEBT_CAPITAL", "REAL"),
    "REVENUE_1Y": DBColumn("REVENUE_1Y", "REAL"),
    "PEG": DBColumn("PEG", "REAL"),
    "P_E": DBColumn("P_E", "REAL"),
    "P_BV": DBColumn("P_BV", "REAL"),
    "FAIR_PRICE": DBColumn("FAIR_PRICE", "REAL"),
    "PRICE_LOW": DBColumn("PRICE_LOW", "REAL"),
    "PRICE_HIGH": DBColumn("PRICE_HIGH", "REAL"),
    "CUR_DIV": DBColumn("CUR_DIV", "REAL", indexed=True),
    "PREV_DIV": DBColumn("PREV_DIV", "REAL"),
    "NUM_DIV_1Y": DBColumn("NUM_DIV_1Y", "INTEGER"),
    "DIV_1Y": DBColumn("DIV_1Y", "REAL"),
    "PAY_DATE": DBColumn("PAY_DATE", "TEXT"),

    "EX_DATE": DBColumn("EX_DATE", "TEXT"),
    "COMPANY": DBColumn("COMPANY", "TEXT"),
    "INDUSTRY": DBColumn("INDUSTRY", "TEXT", indexed=True),
    "UPDATED_AT": DBColumn("UPDATED_AT", "TEXT", extra_sql="NOT NULL")
}
