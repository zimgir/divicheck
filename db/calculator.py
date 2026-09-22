import pandas as pd
from datetime import datetime

from db.schema import SCHEMA

class DBRowCalculator:
    def __init__(self, symbol: str, data: dict):
        self.symbol = symbol
        self.data = data # dict with info, dividends, income_stmt, balance_sheet, cashflow


    def calculate(self) -> dict:
        info = self.data.get("info", {})
        dividends = self.data.get("dividends")
        fin = self.data.get("income_stmt")
        bs = self.data.get("balance_sheet")
        cf = self.data.get("cashflow")
        ttr_1y = self.data.get("ttr_1y")
        ttr_3y = self.data.get("ttr_3y")

        now = pd.Timestamp.now(tz="UTC")
        try:
            s = pd.Series(dividends)
            s.index = pd.to_datetime(s.index)
            naive_idx = s.index.tz_convert(None) if s.index.tz is not None else s.index
            last12 = s[naive_idx >= (pd.Timestamp.now() - pd.Timedelta(days=365))]
            div_1y = float(last12.sum()) if len(last12) else None
            num_div = int(len(last12)) if len(last12) else 0
        except Exception:
            div_1y = None
            num_div = 0

        try:
            pay_date = pd.to_datetime(dividends.index[-1]).date().isoformat() if dividends is not None and len(dividends) else None
            prev_div = float(dividends.iloc[-2]) if dividends is not None and len(dividends) > 1 else None
        except Exception:
            pay_date, prev_div = None, None

        try:
            ex_ts = info.get("exDividendDate")
            ex_date = datetime.fromtimestamp(int(ex_ts), tz=datetime.timezone.utc).date().isoformat() if ex_ts else pay_date
        except Exception:
            ex_date = pay_date

        dgr = {n: self._calc_dividend_growth(dividends, n) for n in (1, 3, 5, 10)}
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        cur_div = float(info.get("trailingAnnualDividendRate") or div_1y or 0) or None

        # Norm yield logic
        raw_y = info.get("dividendYield")
        y1 = None
        if raw_y is not None:
            raw_y = float(raw_y)
            c = float(cur_div) / float(price) if cur_div and price else None
            y1 = raw_y / 100 if c and abs(raw_y / 100 - c) <= abs(raw_y - c) else raw_y
            if y1 > 1: y1 = y1 / 100 # safety

        # chowder
        dgr_5y = dgr[5]
        chowder = float(y1) + float(dgr_5y) if y1 is not None and dgr_5y is not None else None

        rev = self._cell(fin, ["Total Revenue"])
        ni = self._cell(fin, ["Net Income"])
        ebit = self._cell(fin, ["EBIT"])
        debt = self._cell(bs, ["Total Debt"])
        equity = self._cell(bs, ["Total Stockholder Equity", "Total Equity"])
        ca = self._cell(bs, ["Total Current Assets", "Current Assets"])
        cl = self._cell(bs, ["Total Current Liabilities", "Current Liabilities"])
        ocf = self._cell(cf, ["Total Cash From Operating Activities", "Operating Cash Flow"])

        eps = info.get("trailingEps")
        pe = self._div(price, eps) if eps else info.get("trailingPE")
        bv = info.get("bookValue")
        shares = info.get("sharesOutstanding") or info.get("impliedSharesOutstanding")
        eps_growth = info.get("earningsGrowth") or info.get("earningsQuarterlyGrowth")

        result = {
            SCHEMA["SYMBOL"].name: self.symbol,
            SCHEMA["STOCK_TYPE"].name: info.get("quoteType"),
            SCHEMA["COMPANY"].name: info.get("shortName") or info.get("longName"),
            SCHEMA["SECTOR"].name: info.get("sector"),
            SCHEMA["INDUSTRY"].name: info.get("industry"),
            SCHEMA["PRICE"].name: price,
            SCHEMA["FAIR_VALUE"].name: info.get("targetMeanPrice"),
            SCHEMA["YIELD_1Y"].name: y1,
            SCHEMA["YIELD_5Y"].name: self._norm_yield_5y(info.get("fiveYearAvgDividendYield"), cur_div, price),
            SCHEMA["DIV_1Y"].name: div_1y,
            SCHEMA["CUR_DIV"].name: cur_div,
            SCHEMA["NUM_DIV_1Y"].name: num_div,
            SCHEMA["PAY_DATE"].name: pay_date,
            SCHEMA["CHOWDER"].name: chowder,
            SCHEMA["ROE"].name: info.get("returnOnEquity"),
            SCHEMA["PAYOUT_RATIO"].name: info.get("payoutRatio"),
            SCHEMA["DEBT_CAPITAL"].name: info.get("debtToEquity"),
            SCHEMA["DGR_1Y"].name: dgr[1],
            SCHEMA["DGR_3Y"].name: dgr[3],
            SCHEMA["DGR_5Y"].name: dgr[5],
            SCHEMA["DGR_10Y"].name: dgr[10],
            SCHEMA["TTR_1Y"].name: ttr_1y,
            SCHEMA["TTR_3Y"].name: ttr_3y,
            SCHEMA["EPS_1Y"].name: eps_growth,
            SCHEMA["REVENUE_1Y"].name: info.get("revenueGrowth"),
            SCHEMA["NPM"].name: self._div(ni, rev),
            SCHEMA["ROTC"].name: self._div(ebit, float(debt or 0) + float(equity or 0)),
            SCHEMA["CUR_R"].name: self._div(ca, cl),
            SCHEMA["P_E"].name: pe,
            SCHEMA["P_BV"].name: self._div(price, bv) if bv else info.get("priceToBook"),
            SCHEMA["CF_SHARE"].name: self._div(ocf, shares),
            SCHEMA["PEG"].name: self._div(pe, float(eps_growth or 0) * 100) if pe and eps_growth and eps_growth > 0 else None,
            SCHEMA["FAIR_PRICE"].name: info.get("targetMeanPrice"),
            SCHEMA["PRICE_LOW"].name: info.get("fiftyTwoWeekLow"),
            SCHEMA["PRICE_HIGH"].name: info.get("fiftyTwoWeekHigh"),
            SCHEMA["PREV_DIV"].name: prev_div,
            SCHEMA["EX_DATE"].name: ex_date,
            SCHEMA["UPDATED_AT"].name: datetime.now(datetime.timezone.utc).isoformat(),
        }

        return result


    def _cagr(self, start: float, end: float, years: int):
        try:
            if not start or not end or start <= 0 or end <= 0 or years <= 0:
                return None
            return (end / start) ** (1 / years) - 1
        except (TypeError, ZeroDivisionError):
            return None


    def _calc_dividend_growth(self, dividends, years: int):
        try:
            if dividends is None or len(dividends) == 0:
                return None
            s = pd.Series(dividends)
            s.index = pd.to_datetime(s.index)
            yearly = s.groupby(s.index.year).sum().sort_index()
            if len(yearly) and int(yearly.index[-1]) == datetime.now().year:
                yearly = yearly.iloc[:-1]
            if len(yearly) < years + 1:
                return None
            return self._cagr(float(yearly.iloc[-years - 1]), float(yearly.iloc[-1]), years)
        except Exception:
            return None


    def _div(self, a, b):
        try:
            if a is None or b is None or float(b) == 0:
                return None
            return float(a) / float(b)
        except (TypeError, ValueError):
            return None


    def _cell(self, df, names: list[str]):
        try:
            if df is None or len(df) == 0:
                return None
            labels = {str(ix).lower(): ix for ix in df.index}
            for n in names:
                key = labels.get(n.lower())
                if key is not None:
                    v = df.loc[key].iloc[0]
                    return None if v != v else float(v)
            for lbl, ix in labels.items():
                for n in names:
                    if n.lower() in lbl:
                        v = df.loc[ix].iloc[0]
                        return None if v != v else float(v)
            return None
        except Exception:
            return None


    def _norm_yield_5y(self, raw, cur_div, price):
        # reuse or adapt existing logic
        try:
            if raw is None: return None
            raw = float(raw)
            c = float(cur_div) / float(price) if cur_div and price else None
            return raw / 100 if c and abs(raw / 100 - c) <= abs(raw - c) else raw
        except: return None

