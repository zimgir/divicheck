from pathlib import Path

DB_DIR = Path(__file__).resolve().parent.parent / ".db"
DB_DIR.mkdir(exist_ok=True, parents=True)

LOGS_DIR = Path(__file__).resolve().parent.parent / ".logs"
LOGS_DIR.mkdir(exist_ok=True, parents=True)

DB_PATH = DB_DIR / "divicheck.db"

ALL_SYMBOLS_PATH = DB_DIR / "symbols_all.txt"
DIVIDEND_SYMBOLS_PATH = DB_DIR / "symbols_dividend.txt"
FETCH_ROWS_PATH = DB_DIR / "fetch_rows.csv"

FALLBACK_SYMBOLS = ("AAPL", "MSFT", "JNJ", "PG", "KO", "PEP", "XOM", "CVX", "T", "VZ")

