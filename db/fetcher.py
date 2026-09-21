import sys
import time
import pandas as pd
import yfinance as yf
import requests
import logging
import contextlib

from datetime import datetime, timezone
from pathlib import Path

from db.logger import DBLogger, log_streams_to

class LoggerStream:
    def __init__(self, logger, original_stream, is_error=False):
        self.logger = logger
        self.orig = original_stream
        self.is_error = is_error

    def write(self, msg):
        self.orig.write(msg)
        for line in msg.splitlines():
            clean = line.strip()
            if clean:
                if self.is_error:
                    self.logger.error(clean)
                else:
                    self.logger.info(clean)

    def flush(self):
        self.orig.flush()

# ---- pure calc fns (no network) ----

def cagr(start: float, end: float, years: int):
    try:
        if not start or not end or start <= 0 or end <= 0 or years <= 0:
            return None
        return (end / start) ** (1 / years) - 1
    except (TypeError, ZeroDivisionError):
        return None


def calc_dividend_growth(dividends, years: int):
    """CAGR of calendar-year dividend sums over `years` (complete years only)."""
    try:
        if dividends is None or len(dividends) == 0:
            return None
        s = pd.Series(dividends)
        s.index = pd.to_datetime(s.index)
        yearly = s.groupby(s.index.year).sum().sort_index()
        # ponytail: drop partial current year, else DGR always dives mid-year
        if len(yearly) and int(yearly.index[-1]) == datetime.now().year:
            yearly = yearly.iloc[:-1]
        if len(yearly) < years + 1:
            return None
        return cagr(float(yearly.iloc[-years - 1]), float(yearly.iloc[-1]), years)
    except Exception:
        return None


def calc_chowder(dividend_yield, dgr_5y):
    if dividend_yield is None or dgr_5y is None:
        return None
    try:
        return float(dividend_yield) + float(dgr_5y)
    except (TypeError, ValueError):
        return None


def _div(a, b):
    try:
        if a is None or b is None or float(b) == 0:
            return None
        return float(a) / float(b)
    except (TypeError, ValueError):
        return None


def calc_npm(net_income, revenue):
    return _div(net_income, revenue)


def calc_rotc(ebit, total_debt, total_equity):
    if ebit is None or total_debt is None or total_equity is None:
        return None
    return _div(ebit, float(total_debt) + float(total_equity))


def calc_cur_ratio(current_assets, current_liabilities):
    return _div(current_assets, current_liabilities)


def calc_peg(pe, eps_growth):
    """eps_growth as decimal (0.1 = 10%). None if growth <= 0."""
    try:
        if pe is None or eps_growth is None or float(eps_growth) <= 0:
            return None
        return float(pe) / (float(eps_growth) * 100)
    except (TypeError, ValueError):
        return None


def calc_total_return(start_price, end_price, dividends):
    return _div(float(end_price) - float(start_price) + float(dividends or 0), start_price)


# ---- yfinance helpers ----

def _cell(df, names: list[str]):
    """First matching row label -> latest column value. None-safe."""
    try:
        if df is None or len(df) == 0:
            return None
        labels = {str(ix).lower(): ix for ix in df.index}
        for n in names:
            key = labels.get(n.lower())
            if key is not None:
                v = df.loc[key].iloc[0]
                return None if v != v else float(v)  # NaN -> None
        # fallback: substring match
        for lbl, ix in labels.items():
            for n in names:
                if n.lower() in lbl:
                    v = df.loc[ix].iloc[0]
                    return None if v != v else float(v)
        return None
    except Exception:
        return None


def _pct(x):
    """yfinance yields come back percent-scale (2.42 = 2.42%). Normalize to decimal."""
    try:
        if x is None:
            return None
        x = float(x)
        return x / 100 if x > 1 else x
    except (TypeError, ValueError):
        return None


def _norm_yield(raw, cur_div, price):
    """Pick scale (raw vs raw/100) closest to CUR_DIV/PRICE cross-check."""
    try:
        if raw is None:
            return None
        raw = float(raw)
        c = None
        if cur_div and price:
            c = float(cur_div) / float(price)
        if c is not None and c > 0:
            return raw / 100 if abs(raw / 100 - c) <= abs(raw - c) else raw
        return raw / 100  # observed API default: percent-scale
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def _ttr(ticker, dividends) -> tuple:
    """(ttr_1y, ttr_3y) from single 3y history call."""
    logger = DBLogger.get_logger("fetch_all", reset=False)
    try:
        hist = DBDataFetcher._retry_on_rate_limit(lambda: ticker.history(period="3y", auto_adjust=False))
        if hist is None or len(hist) == 0:
            return None, None
        close = hist["Close"].dropna()
        if len(close) < 2:
            return None, None
        now = close.iloc[-1]
        idx = close.index.tz_convert(None) if close.index.tz is not None else close.index

        def price_asof(days: int):
            cutoff = idx[-1] - pd.Timedelta(days=days)
            past = close[idx <= cutoff]
            return float(past.iloc[-1]) if len(past) else float(close.iloc[0])

        def div_asof(days: int):
            try:
                if dividends is None or len(dividends) == 0:
                    return 0.0
                s = pd.Series(dividends)
                s.index = pd.to_datetime(s.index).tz_convert(None) if s.index.tz is not None else pd.to_datetime(s.index)
                return float(s[s.index >= (idx[-1] - pd.Timedelta(days=days))].sum())
            except Exception:
                return 0.0
        
        p1, p3 = price_asof(365), price_asof(365 * 3)
        return (
            calc_total_return(p1, now, div_asof(365)),
            calc_total_return(p3, now, div_asof(365 * 3)),
        )
    except Exception as e:
        logger.error(f"TTR fail: {e}")
        return None, None


def is_payer(info: dict) -> bool:
    try:
        return float(info.get("dividendYield") or 0) > 0 or float(info.get("trailingAnnualDividendRate") or 0) > 0
    except (TypeError, ValueError):
        return False


def fetch_symbol(symbol: str) -> dict | None:
    """Full fetch for one symbol. None if non-payer or fail."""
    logger = DBLogger.get_logger("fetch_all", reset=False)
    symbol = symbol.strip().upper()
    if not symbol:
        return None
    try:
        t = yf.Ticker(symbol)
        info = DBDataFetcher._retry_on_rate_limit(lambda: t.info or {})
    except Exception as e:
        logger.error(f"{symbol} info fail: {e}")
        return None
    if not is_payer(info):
        logger.error(f"{symbol} skip: non-payer")
        return None
    try:
        dividends = DBDataFetcher._retry_on_rate_limit(lambda: t.dividends)
        if dividends is None:
            dividends = pd.Series(dtype=float)
        now = pd.Timestamp.now(tz="UTC")
        cutoff = now.tz_convert(None) if now.tz is not None else now
        try:
            s = pd.Series(dividends)
            s.index = pd.to_datetime(s.index)
            naive_idx = s.index.tz_convert(None) if s.index.tz is not None else s.index
            last12 = s[naive_idx >= (pd.Timestamp.now() - pd.Timedelta(days=365))]
        except Exception:
            last12 = pd.Series(dtype=float)
        div_1y = float(last12.sum()) if len(last12) else None
        num_div = int(len(last12)) if len(last12) else 0
        try:
            pay_date = pd.to_datetime(dividends.index[-1]).date().isoformat() if len(dividends) else None
            prev_div = float(dividends.iloc[-2]) if len(dividends) > 1 else None
        except Exception:
            pay_date, prev_div = None, None
        try:
            ex_ts = info.get("exDividendDate")
            ex_date = datetime.fromtimestamp(int(ex_ts), tz=timezone.utc).date().isoformat() if ex_ts else pay_date
        except Exception:
            ex_date = pay_date

        dgr = {n: calc_dividend_growth(dividends, n) for n in (1, 3, 5, 10)}
        price = info.get("currentPrice") or info.get("regularMarketPrice")
        cur_div = float(info.get("trailingAnnualDividendRate") or div_1y or 0) or None
        y1 = _norm_yield(info.get("dividendYield"), cur_div, price)
        chowder = calc_chowder(y1, dgr[5])

        try:
            fin = DBDataFetcher._retry_on_rate_limit(lambda: t.income_stmt if getattr(t, "income_stmt", None) is not None and len(getattr(t, "income_stmt")) else t.financials)
        except Exception:
            fin = None
        try:
            bs = DBDataFetcher._retry_on_rate_limit(lambda: t.balance_sheet)
        except Exception:
            bs = None
        try:
            cf = DBDataFetcher._retry_on_rate_limit(lambda: t.cashflow)
        except Exception:
            cf = None

        rev = _cell(fin, ["Total Revenue"])
        ni = _cell(fin, ["Net Income"])
        ebit = _cell(fin, ["EBIT"])
        debt = _cell(bs, ["Total Debt"])
        equity = _cell(bs, ["Total Stockholder Equity", "Total Equity"])
        ca = _cell(bs, ["Total Current Assets", "Current Assets"])
        cl = _cell(bs, ["Total Current Liabilities", "Current Liabilities"])
        ocf = _cell(cf, ["Total Cash From Operating Activities", "Operating Cash Flow"])

        eps = info.get("trailingEps")
        pe = _div(price, eps) if eps else info.get("trailingPE")
        bv = info.get("bookValue")
        shares = info.get("sharesOutstanding") or info.get("impliedSharesOutstanding")
        eps_growth = info.get("earningsGrowth") or info.get("earningsQuarterlyGrowth")

        ttr_1y, ttr_3y = _ttr(t, dividends)

        return {
            "SYMBOL": symbol,
            "STOCK_TYPE": info.get("quoteType"),
            "COMPANY": info.get("shortName") or info.get("longName"),
            "SECTOR": info.get("sector"),
            "INDUSTRY": info.get("industry"),
            "PRICE": price,
            "FAIR_VALUE": info.get("targetMeanPrice"),
            "YIELD_1Y": y1,
            "YIELD_5Y": _norm_yield(info.get("fiveYearAvgDividendYield"), cur_div, price),
            "DIV_1Y": div_1y,
            "CUR_DIV": cur_div,
            "NUM_DIV_1Y": num_div,
            "PAY_DATE": pay_date,
            "CHOWDER": chowder,
            "ROE": info.get("returnOnEquity"),
            "PAYOUT_RATIO": info.get("payoutRatio"),
            "DEBT_CAPITAL": info.get("debtToEquity"),
            "DGR_1Y": dgr[1],
            "DGR_3Y": dgr[3],
            "DGR_5Y": dgr[5],
            "DGR_10Y": dgr[10],
            "TTR_1Y": ttr_1y,
            "TTR_3Y": ttr_3y,
            "EPS_1Y": eps_growth,
            "REVENUE_1Y": info.get("revenueGrowth"),
            "NPM": calc_npm(ni, rev),
            "ROTC": calc_rotc(ebit, debt, equity),
            "CUR_R": calc_cur_ratio(ca, cl),
            "P_E": pe,
            "P_BV": _div(price, bv) if bv else info.get("priceToBook"),
            "CF_SHARE": _div(ocf, shares),
            "PEG": calc_peg(pe, eps_growth),
            "FAIR_PRICE": info.get("targetMeanPrice"),
            "PRICE_LOW": info.get("fiftyTwoWeekLow"),
            "PRICE_HIGH": info.get("fiftyTwoWeekHigh"),
            "PREV_DIV": prev_div,
            "EX_DATE": ex_date,
            "UPDATED_AT": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        logger.error(f"{symbol} fetch fail: {e}")
        return None


def fetch_all(symbols: list[str], sleep: float = 1.0, batch: int = 50) -> list[dict]:
    """Two-pass: cheap info scan filters payers, then full fetch."""
    logger = DBLogger.get_logger("fetch_all", reset=True)
    symbols = [s.strip().upper() for s in symbols if s and s.strip()]
    payers: list[str] = []
    for i in range(0, len(symbols), batch):
        for sym in symbols[i : i + batch]:
            try:
                info = DBDataFetcher._retry_on_rate_limit(lambda s=sym: yf.Ticker(s).info or {})
                if is_payer(info):
                    payers.append(sym)
                else:
                    logger.error(f"{sym} skip: non-payer")
            except Exception as e:
                logger.error(f"{sym} scan fail: {e}")
        if sleep and i + batch < len(symbols):
            time.sleep(sleep)
    rows: list[dict] = []
    for i, sym in enumerate(payers):
        row = fetch_symbol(sym)
        if row:
            rows.append(row)
        if sleep and (i + 1) % 10 == 0:
            time.sleep(sleep)
    return rows


class DBDataFetcher:
    @staticmethod
    def _retry_on_rate_limit(fn, attempts: int = 3):
        delay = 1.0
        for i in range(attempts):
            try:
                return fn()
            except Exception as e:
                if "429" in str(e):
                    time.sleep(60)
                    continue
                if i == attempts - 1:
                    raise
                time.sleep(delay)
                delay *= 2
        raise Exception("Max retries exceeded")


    def fetch_all_symbols(self, output_path: str = "symbols_all.txt") -> list[str]:
        r = requests.get("https://scanner.tradingview.com/america/scan", timeout=30)
        symbols = [item["s"].split(":")[-1].split("/")[0] for item in r.json()["data"]]
        Path(output_path).write_text("\n".join(symbols))
        return symbols


    def filter_dividend_symbols(self, symbols: list[str], last_n_years: int = 5, batch_size: int = 40, sleep: float = 1.0, output_path: str = "symbols_dividend.txt") -> list[str]:
        logger = DBLogger.get_logger("filter_divident", reset=True)

        with log_streams_to(logger):
            logger.info(f"Start proccessing {len(symbols)} symbols")

            dividend_symbols = []

            out = Path(output_path)
            if out.exists():
                out.unlink()

            current_year = datetime.now().year

            try:
                for i in range(0, len(symbols), batch_size):
                    batch = symbols[i : i + batch_size]
                    try:
                        tickers_obj = yf.Tickers(" ".join(batch))
                        for sym in batch:

                            try:
                                ticker = tickers_obj.tickers[sym]
                                divs = DBDataFetcher._retry_on_rate_limit(lambda: ticker.dividends)
                                if not divs.empty:
                                    paying_years = sorted([
                                        y for y in divs[divs > 0].index.year.unique() if y < current_year
                                    ])
                                    paying_years_set = set(paying_years)
                                    if all((current_year - j) in paying_years_set for j in range(1, last_n_years + 1)):
                                        dividend_symbols.append(sym)
                                        with open(out, "a") as f:
                                            f.write(sym + "\n")

                            except KeyboardInterrupt:
                                raise
                            except Exception as e:
                                logger.error(f"{sym} inner consecutive filter fail: {e}")

                        DBLogger.print_progress(min(i + batch_size, len(symbols)), len(symbols))

                    except KeyboardInterrupt:
                        raise
                    except Exception as e:
                        logger.error(f"Batch processing failed for {batch}: {e}")
                        time.sleep(5 * sleep)

                        continue
                    if sleep and (i + batch_size < len(symbols)):
                        time.sleep(sleep)

            except KeyboardInterrupt:
                print("Got KeyboardInterrupt stopping...")

            logger.info(f"Done processing {len(dividend_symbols)} symbols")

            return dividend_symbols
