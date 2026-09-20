"""SQLDBController - unified database layer for stock data."""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional


class SQLDBController:
    """Single controller for all stock database operations."""

    COLUMNS = [
        "SYMBOL", "STOCK_TYPE", "COMPANY", "SECTOR", "INDUSTRY",
        "PRICE", "FAIR_VALUE", "YIELD_1Y", "YIELD_5Y", "DIV_1Y",
        "NUM_DIV_1Y", "PAY_DATE", "CHOWDER", "ROE", "PAYOUT_RATIO",
        "DEBT_CAPITAL", "DGR_1Y", "DGR_3Y", "DGR_5Y", "DGR_10Y",
        "TTR_1Y", "TTR_3Y", "EPS_1Y", "REVENUE_1Y", "NPM", "ROTC",
        "CUR_R", "P_E", "P_BV", "CF_SHARE", "PEG", "FAIR_PRICE",
        "PRICE_LOW", "PRICE_HIGH", "PREV_DIV", "EX_DATE", "UPDATED_AT"
    ]

    CREATE_TABLE_SQL = """CREATE TABLE IF NOT EXISTS stocks (
        SYMBOL TEXT PRIMARY KEY,
        STOCK_TYPE TEXT,
        COMPANY TEXT,
        SECTOR TEXT,
        INDUSTRY TEXT,
        PRICE REAL,
        FAIR_VALUE REAL,
        YIELD_1Y REAL,
        YIELD_5Y REAL,
        DIV_1Y REAL,
        CUR_DIV REAL,
        NUM_DIV_1Y INTEGER,
        PAY_DATE TEXT,
        CHOWDER REAL,
        ROE REAL,
        PAYOUT_RATIO REAL,
        DEBT_CAPITAL REAL,
        DGR_1Y REAL,
        DGR_3Y REAL,
        DGR_5Y REAL,
        DGR_10Y REAL,
        TTR_1Y REAL,
        TTR_3Y REAL,
        EPS_1Y REAL,
        REVENUE_1Y REAL,
        NPM REAL,
        ROTC REAL,
        CUR_R REAL,
        P_E REAL,
        P_BV REAL,
        CF_SHARE REAL,
        PEG REAL,
        FAIR_PRICE REAL,
        PRICE_LOW REAL,
        PRICE_HIGH REAL,
        PREV_DIV REAL,
        EX_DATE TEXT,
        UPDATED_AT TEXT NOT NULL
    )"""

    INDEX_SQL = [
        "CREATE INDEX IF NOT EXISTS idx_stocks_yield ON stocks(YIELD_1Y)",
        "CREATE INDEX IF NOT EXISTS idx_stocks_sector ON stocks(SECTOR)",
        "CREATE INDEX IF NOT EXISTS idx_stocks_industry ON stocks(INDUSTRY)",
        "CREATE INDEX IF NOT EXISTS idx_stocks_dgr ON stocks(DGR_5Y)",
        "CREATE INDEX IF NOT EXISTS idx_stocks_div ON stocks(CUR_DIV)",
    ]

    DROP_TABLE_SQL = "DROP TABLE IF EXISTS stocks"

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None

    def get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA journal_mode = WAL")
            self._conn.execute("PRAGMA synchronous = NORMAL")
            self._conn.execute("PRAGMA foreign_keys = ON")
            self._conn.execute("PRAGMA busy_timeout = 5000")
        return self._conn

    def init_db(self) -> None:
        con = self.get_connection()
        con.execute(self.CREATE_TABLE_SQL)
        for sql in self.INDEX_SQL:
            con.execute(sql)
        con.commit()

    def upsert_many(self, rows: List[Dict[str, any]]) -> int:
        if not rows:
            return 0
        con = self.get_connection()
        
        # Use COLUMNS for conflict resolution
        cols = self.COLUMNS
        upsert_sql = (
            f"INSERT INTO stocks ({', '.join(cols)}) VALUES ({', '.join(['?'] * len(cols))}) "
            f"ON CONFLICT(SYMBOL) DO UPDATE SET {', '.join(f'{c}=excluded.{c}' for c in cols if c != 'SYMBOL')}"
        )
        
        with con:
            con.executemany(upsert_sql, [[row.get(c) for c in cols] for row in rows])
        return len(rows)

    def delete_missing(self, symbols: List[str]) -> int:
        if not symbols:
            return 0
        con = self.get_connection()
        placeholders = ",".join(["?"] * len(symbols))
        sql = f"DELETE FROM stocks WHERE SYMBOL NOT IN ({placeholders})"
        with con:
            cur = con.execute(sql, symbols)
        return cur.rowcount

    def fetch_all_rows(self) -> List[sqlite3.Row]:
        con = self.get_connection()
        return con.execute("SELECT * FROM stocks").fetchall()

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
