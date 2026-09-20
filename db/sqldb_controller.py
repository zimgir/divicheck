"""SQLDBController - unified database layer for stock data."""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from db import schema


class SQLDBController:
    """Single controller for all stock database operations."""

    COLUMNS = [c.name for c in schema.SCHEMA.values()]

    # Generate SQL
    CREATE_TABLE_SQL = f"""CREATE TABLE IF NOT EXISTS stocks (
        {", ".join([f"{c.name} {c.data_type} {'PRIMARY KEY' if c.is_pk else ''} {c.extra_sql}".strip() for c in schema.SCHEMA.values()])}
    )"""

    INDEX_SQL = [
        f"CREATE INDEX IF NOT EXISTS idx_stocks_{c.name.lower()} ON stocks({c.name})"
        for c in schema.SCHEMA.values() if c.indexed
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
