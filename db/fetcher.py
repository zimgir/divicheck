import time
import pandas as pd
import yfinance as yf
import requests

from datetime import datetime
from pathlib import Path

from db.logger import DBLogger, log_streams_to
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


    def filter_dividend_symbols(self, symbols: list[str], last_n_years: int = 5, batch_size: int = 40, sleep: float = 1.0, output_path: str = "symbols_dividend.txt") -> list[str]:
        logger = DBLogger.get_logger("filter_divident", reset=True)

        with log_streams_to(logger):
            print(f"Start proccessing {len(symbols)} symbols")

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
                                divs = self._retry_on_rate_limit(lambda: ticker.dividends)
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
            print(f"Done processing {len(dividend_symbols)} symbols")
            return dividend_symbols


    def _process_rows(self, rows: list[dict]) -> list[dict]:
        processed_rows = []
        for row in rows:
            new_row = row.copy()
            for k, v in row.items():
                if k not in SCHEMA: continue
                col_def = SCHEMA[k]
                if col_def.data_type == "REAL":
                    if v is None:
                        new_row[k] = None
                    else:
                        val = float(v)
                        if col_def.unit == "%":
                            val = val * 100
                        new_row[k] = round(val, 4)
                else:
                    new_row[k] = v
            processed_rows.append(new_row)
        return processed_rows

    def fetch_db_rows(self, symbols: list[str], output_csv: Path, batch_size: int = 40, sleep: float = 1.0) -> Path:
        """Fetch/calculate in batches, write directly to intermediate CSV."""
        logger = DBLogger.get_logger("fetch_db_rows", reset=True)
        with log_streams_to(logger):
            print(f"Start fetching rows for {len(symbols)} symbols. Output: {output_csv}")
            first = True
            if output_csv.exists():
                output_csv.unlink()

            for i in range(0, len(symbols), batch_size):
                batch = symbols[i : i + batch_size]

                rows = []
                for sym in batch:
                    raw_data = self._fetch_raw_data(sym)
                    if raw_data:
                        calc = DBRowCalculator(sym, raw_data)
                        rows.append(calc.calculate())
                if rows:
                    processed_rows = self._process_rows(rows)
                    df = pd.DataFrame(processed_rows)
                    df.to_csv(output_csv, mode='a', index=False, header=first)
                    first = False

                DBLogger.print_progress(min(i + batch_size, len(symbols)), len(symbols))
                if sleep and (i + batch_size < len(symbols)):
                    time.sleep(sleep)

            print(f"Done fetching {len(processed_rows)}. Saved to {output_csv}")
            return output_csv


    def _fetch_raw_data(self, symbol: str) -> dict | None:
        """Fetch all raw data for a symbol."""
        logger = DBLogger.get_logger("fetch_all", reset=False)
        symbol = symbol.strip().upper()
        if not symbol: return None
        try:
            t = yf.Ticker(symbol)
            info = self._retry_on_rate_limit(lambda: t.info or {})
            if not self._is_payer(info):
                logger.error(f"{symbol} skip: non-payer")
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
            logger.error(f"{symbol} fetch raw data fail: {e}")
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



