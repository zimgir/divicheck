# ----------------------------
# Column explanations
# ----------------------------
COL_DESC = {
    "Price": "Current stock price.",
    "Div Yield": "Annual dividend yield percentage. Higher is better for income investors.",
    "5Y Avg Yield": "Average dividend yield over last 5 years.",
    "Current Div": "Most recent dividend payment.",
    "Payouts/Year": "Number of dividend payments per year.",
    "Annualized": "Annualized dividend amount.",
    "Low": "52-week low price.",
    "High": "52-week high price.",
    "Chowder Number": "Dividend Yield + Dividend Growth Rate. Measures income + growth.",
    "DGR 1Y": "Dividend Growth Rate over 1 year.",
    "DGR 3Y": "Dividend Growth Rate over 3 years.",
    "DGR 5Y": "Dividend Growth Rate over 5 years.",
    "DGR 10Y": "Dividend Growth Rate over 10 years.",
    "TTR 1Y": "Total return over 1 year.",
    "TTR 3Y": "Total return over 3 years.",
    "FV (Peter Lynch)": "Fair value estimate using Peter Lynch method.",
    "FV (Peter Lynch) %": "Percent over/undervalued relative to fair value.",
    "EPS 1Y": "Earnings per share growth (1 year).",
    "Revenue 1Y": "Revenue growth over last year.",
    "NPM": "Net profit margin. Measures profitability.",
    "CF/Share": "Cash flow per share.",
    "ROE": "Return on equity. Capital efficiency.",
    "Current R": "Current ratio. Liquidity measure.",
    "Debt/Capital": "Debt to total capital. Lower is safer.",
    "ROTC": "Return on total capital.",
    "P/E": "Price-to-earnings ratio. Valuation metric.",
    "P/BV": "Price-to-book value ratio.",
    "PEG": "Price / Earnings to Growth ratio. Valuation adjusted for growth.",
    "Beta": "Volatility compared to market.",
}

COL_LOWER_IS_BETTER = {
    "Debt/Capital",
    "P/E",
    "PEG",
    "P/BV"
}


COL_SECTOR = "Sector"

COL_FAIR_VALUE_PCT = "FV (Peter Lynch) %"

COL_ANNUAL_YIELD = "Annualized"
COL_ANNUAL_EPS = "EPS 1Y"

COL_SAFETY_SCORE_INPUTS = {
    COL_ANNUAL_EPS,
    "Debt/Capital",
    "ROE",
    "CF/Share",
}


COL_TOTAL_SCORE = "_total_score"
COL_SAFETY_SCORE = "_safety_score"
COL_VALUE_SCORE = "_value_score"
COL_PAYOUT_RATIO = "_payout_ratio"

COL_SECTOR_RANK = "_sector_rank"


