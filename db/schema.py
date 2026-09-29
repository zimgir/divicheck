from dataclasses import dataclass

@dataclass
class DBColumn:
    name: str
    data_type: str
    is_pk: bool = False
    indexed: bool = False
    extra_sql: str = ""
    unit: str = ""

SCHEMA = {
    "SYMBOL": DBColumn("SYMBOL", "TEXT", is_pk=True),
    "SECTOR": DBColumn("SECTOR", "TEXT", indexed=True),
    "PRICE": DBColumn("PRICE", "REAL", unit="$"),
    "FAIR_VALUE": DBColumn("FAIR_VALUE", "REAL", unit="%"),
    "YIELD_1Y": DBColumn("YIELD_1Y", "REAL", indexed=True, unit="%"),
    "YIELD_5Y": DBColumn("YIELD_5Y", "REAL", unit="%"),
    "TTR_1Y": DBColumn("TTR_1Y", "REAL", unit="%"),
    "TTR_3Y": DBColumn("TTR_3Y", "REAL", unit="%"),
    "DGR_1Y": DBColumn("DGR_1Y", "REAL", unit="%"),
    "DGR_3Y": DBColumn("DGR_3Y", "REAL", unit="%"),
    "DGR_5Y": DBColumn("DGR_5Y", "REAL", indexed=True, unit="%"),
    "DGR_10Y": DBColumn("DGR_10Y", "REAL", unit="%"),
    "CHOWDER": DBColumn("CHOWDER", "REAL"),
    "ROE": DBColumn("ROE", "REAL", unit="%"),
    "NPM": DBColumn("NPM", "REAL", unit="%"),
    "ROTC": DBColumn("ROTC", "REAL", unit="%"),
    "CUR_R": DBColumn("CUR_R", "REAL"),
    "EPS_1Y": DBColumn("EPS_1Y", "REAL", unit="%"),
    "CF_SHARE": DBColumn("CF_SHARE", "REAL", unit="$"),
    "PAYOUT_RATIO": DBColumn("PAYOUT_RATIO", "REAL"),
    "DEBT_CAPITAL": DBColumn("DEBT_CAPITAL", "REAL"),
    "REVENUE_1Y": DBColumn("REVENUE_1Y", "REAL", unit="%"),
    "PEG": DBColumn("PEG", "REAL"),
    "P_E": DBColumn("P_E", "REAL"),
    "P_BV": DBColumn("P_BV", "REAL"),
    "FAIR_PRICE": DBColumn("FAIR_PRICE", "REAL", unit="$"),
    "PRICE_LOW": DBColumn("PRICE_LOW", "REAL", unit="$"),
    "PRICE_HIGH": DBColumn("PRICE_HIGH", "REAL", unit="$"),
    "CUR_DIV": DBColumn("CUR_DIV", "REAL", indexed=True, unit="$"),
    "PREV_DIV": DBColumn("PREV_DIV", "REAL", unit="$"),
    "NUM_DIV_1Y": DBColumn("NUM_DIV_1Y", "INTEGER"),
    "DIV_1Y": DBColumn("DIV_1Y", "REAL", unit="$"),
    "PAY_DATE": DBColumn("PAY_DATE", "TEXT", unit="date"),
    "EX_DATE": DBColumn("EX_DATE", "TEXT", unit="date"),
    "COMPANY": DBColumn("COMPANY", "TEXT"),
    "INDUSTRY": DBColumn("INDUSTRY", "TEXT", indexed=True),
    "UPDATED_AT": DBColumn("UPDATED_AT", "TEXT", extra_sql="NOT NULL")
}

COL_INFO = {
    "SYMBOL": "Stock Symbol",
    "SECTOR": "Company sector",
    "PRICE": "Current share price",
    "FAIR_VALUE": "Percent over/under valued relative to fair value using Peter Lynch method",
    "YIELD_1Y": "Share divident yield % per year",
    "YIELD_5Y": "Share yield % per year on 5 years average",
    "TTR_1Y": "Total return over 1 year",
    "TTR_3Y": "Total return over 3 years",
    "DGR_1Y": "Dividend Growth Rate over 1 years",
    "DGR_3Y": "Dividend Growth Rate over 3 years",
    "DGR_5Y": "Dividend Growth Rate over 5 years",
    "DGR_10Y": "Dividend Growth Rate over 10 years",
    "CHOWDER": "Dividend Yield + Dividend Growth Rate. Measures income + growth",
    "ROE": "Return on equity. Capital efficiency",
    "NPM": "Net profit margin. Measures profitability",
    "ROTC": "Return on total capital",
    "CUR_R": "Current ratio. Liquidity measure",
    "EPS_1Y": "Earnings per share growth 1 year",
    "CF_SHARE": "Cash flow per share",
    "PAYOUT_RATIO": "Anual divident to cashflow per share ratio",
    "DEBT_CAPITAL": "Debt to total capital",
    "REVENUE_1Y": "Revenue growth over last year",
    "PEG": "Price / Earnings to Growth ratio",
    "P_E": "Price-to-earnings ratio",
    "P_BV": "Price-to-book value ratio",
    "FAIR_PRICE": "Fair price estimate using Peter Lynch method",
    "PRICE_LOW": "52-week low price",
    "PRICE_HIGH": "52-week high price",
    "CUR_DIV": "Most recent divident yield",
    "PREV_DIV": "Previous divident yield",
    "NUM_DIV_1Y": "Number of divident payouts per year",
    "DIV_1Y": "Total divident yield over 1 year",
    "PAY_DATE": "Date of next divident payment",
    "EX_DATE": "Ex dividend date",
    "COMPANY": "Company name",
    "INDUSTRY": "Company industry",
    "UPDATED_AT": "Last update time"
}
