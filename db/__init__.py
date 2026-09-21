from pathlib import Path

DB_DIR = Path(__file__).resolve().parent.parent / ".db"
ALL_SYMBOLS_PATH = DB_DIR / "symbols_all.txt"
DIVIDEND_SYMBOLS_PATH = DB_DIR / "symbols_dividend.txt"
DB_PATH = DB_DIR / "divicheck.db"
FALLBACK_SYMBOLS = ("AAPL", "MSFT", "JNJ", "PG", "KO", "PEP", "XOM", "CVX", "T", "VZ")
