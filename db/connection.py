import sqlite3
from pathlib import Path

from .schema import CREATE_TABLE_SQL, INDEX_SQL


def get_connection(db_path: str | Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(db_path))
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode = WAL")
    con.execute("PRAGMA synchronous = NORMAL")
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA busy_timeout = 5000")
    return con


def init_db(con: sqlite3.Connection) -> None:
    con.execute(CREATE_TABLE_SQL)
    for sql in INDEX_SQL:
        con.execute(sql)
    con.commit()
