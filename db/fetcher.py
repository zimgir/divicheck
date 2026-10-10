import sys
import time
import pandas as pd
import yfinance as yf
import requests

from datetime import datetime
from pathlib import Path

from db.logger import DBLogger
from db.calculator import DBRowCalculator
from db.schema import SCHEMA

class DBDataFetcher:

    def __init__(self):
        pass


    def fetch_all_symbols(self, output_path: str = "symbols_all.txt") -> list[str]:
        r = requests.get("https://scanner.tradingview.com/america/scan", timeout=30)
        symbols = [item["s"].split(":")[-1].split("/")[0] for item in r.json()["data"]]
        Path(output_path).write_text("\n".join(symbols))
        return symbols


    def _filter_divident_symbols(self, divs: pd.Series, last_n_years: int = 5) -> bool:
        if divs is None or divs.empty:
            return False
        current_year = datetime.now().year
        series = pd.Series(divs)
        series.index = pd.to_datetime(series.index)
        yearly_dividends = series.groupby(series.index.year).sum().sort_index()
        target_years = [current_year - j for j in range(last_n_years, 0, -1)]
        if not all(y in yearly_dividends.index for y in target_years):
            return False
        vals = [yearly_dividends[y] for y in target_years]
        if not all(v > 0 for v in vals):
            return False
        if not all(vals[k] > vals[k-1] for k in range(1, len(vals))):
            return False
        return True


    def fetch_divident_symbols(self, symbols: list[str], last_n_years: int = 5, batch_size: int = 40, sleep: float = 1.0, output_path: str = "symbols_dividend.txt") -> list[str]:
        print(f"Start proccessing {len(symbols)} symbols")

        dividend_symbols = []

        out = Path(output_path)
        if out.exists():
            out.unlink()
        try:
            for i in range(0, len(symbols), batch_size):
                batch = symbols[i : i + batch_size]
                try:
                    tickers_obj = yf.Tickers(" ".join(batch))
                    for sym in batch:

                        try:
                            ticker = tickers_obj.tickers[sym]
                            divs = self._retry_on_rate_limit(lambda: ticker.dividends)
                            if self._filter_divident_symbols(divs, last_n_years=last_n_years):
                                dividend_symbols.append(sym)
                                with open(out, "a") as f:
                                    f.write(sym + "\n")

                        except KeyboardInterrupt:
                            raise
                        except Exception as e:
                            print(f"{sym} inner consecutive filter fail: {e}", file=sys.stderr)
                    DBLogger.print_progress(min(i + batch_size, len(symbols)), len(symbols), "Filtering dividend symbols")
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    print(f"Batch processing failed for {batch}: {e}", file=sys.stderr)
                    time.sleep(5 * sleep)
                    continue
                if sleep and (i + batch_size < len(symbols)):
                    time.sleep(sleep)
        except KeyboardInterrupt:
            print("Got KeyboardInterrupt stopping...")
        print(f"Done processing {len(dividend_symbols)} symbols")
        return dividend_symbols


    def fetch_db_rows(self, symbols: list[str], output_csv: Path, batch_size: int = 40, sleep: float = 1.0) -> Path:
        """Fetch/calculate in batches, write directly to intermediate CSV."""
        print(f"Start fetching rows for {len(symbols)} symbols. Output: {output_csv}")
        first = True
        if output_csv.exists():
            output_csv.unlink()

        total = len(symbols)
        total_fetched = 0
        DBLogger.print_progress(0, total, "Fetching rows")
        for i in range(0, total, batch_size):
            batch = symbols[i : i + batch_size]

            rows = []
            for j, sym in enumerate(batch):
                raw_data = self._fetch_raw_data(sym)
                if raw_data:
                    calc = DBRowCalculator(sym, raw_data)
                    rows.append(calc.calculate())
                DBLogger.print_progress(min(i + j + 1, total), total, f"Fetching {sym}")
            if rows:
                df = pd.DataFrame(rows)
                df.to_csv(output_csv, mode='a', index=False, header=first)
                first = False
                total_fetched += len(rows)

            if sleep and (i + batch_size < total):
                time.sleep(sleep)

        print(f"Done fetching {total_fetched}. Saved to {output_csv}")
        return output_csv


    def _fetch_raw_data(self, symbol: str) -> dict | None:
        """Fetch all raw data for a symbol."""
        symbol = symbol.strip().upper()
        if not symbol: return None
        try:
            t = yf.Ticker(symbol)
            info = self._retry_on_rate_limit(lambda: t.info or {})
            if not self._is_payer(info):
                print(f"{symbol} skip: non-payer", file=sys.stderr)
                return None
            dividends = self._retry_on_rate_limit(lambda: t.dividends)
            if dividends is None: dividends = pd.Series(dtype=float)

            try:
                fin = self._retry_on_rate_limit(lambda: t.income_stmt if getattr(t, "income_stmt", None) is not None and len(getattr(t, "income_stmt")) else t.financials)
            except Exception: fin = None
            try: bs = self._retry_on_rate_limit(lambda: t.balance_sheet)
            except Exception: bs = None
            try: cf = self._retry_on_rate_limit(lambda: t.cashflow)
            except Exception: cf = None

            try:
                hist = self._retry_on_rate_limit(lambda: t.history(period="3y", auto_adjust=False))
            except Exception:
                hist = None

            return {
                "info": info,
                "dividends": dividends,
                "income_stmt": fin,
                "balance_sheet": bs,
                "cashflow": cf,
                "history": hist
            }
        except Exception as e:
            print(f"{symbol} fetch raw data fail: {e}", file=sys.stderr)
            return None


    def _retry_on_rate_limit(self, fn, attempts: int = 3):
        delay = 1.0
        for i in range(attempts):
            try:
                return fn()
            except Exception as e:
                if "429" in str(e):
                    print(f"Rate limit hit (429). Retrying in 60s. Attempt {i+1}/{attempts}")
                    time.sleep(60)
                    continue
                print(f"Error on attempt {i+1}/{attempts}: {e}")
                if i == attempts - 1:
                    raise
                time.sleep(delay)
                delay *= 2
        raise Exception("Max rate limit retries exceeded")


    def _is_payer(self, info: dict) -> bool:
        try:
            return float(info.get("dividendYield") or 0) > 0 or float(info.get("trailingAnnualDividendRate") or 0) > 0
        except (TypeError, ValueError):
            return False



