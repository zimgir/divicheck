import sqlite3

from .schema import COLUMNS

_UPSERT_SQL = (
    f"INSERT INTO stocks ({', '.join(COLUMNS)}) VALUES ({', '.join(':' + c for c in COLUMNS)}) "
    f"ON CONFLICT(SYMBOL) DO UPDATE SET {', '.join(f'{c}=excluded.{c}' for c in COLUMNS if c != 'SYMBOL')}"
)


def _row(row: dict) -> dict:
    return {c: row.get(c) for c in COLUMNS}


def upsert_stock(con: sqlite3.Connection, row: dict, commit: bool = True) -> None:
    con.execute(_UPSERT_SQL, _row(row))
    if commit:
        con.commit()


def upsert_many(con: sqlite3.Connection, rows: list[dict]) -> int:
    with con:
        con.executemany(_UPSERT_SQL, [_row(r) for r in rows])
    return len(rows)


def delete_missing(con: sqlite3.Connection, symbols: list[str]) -> int:
    if not symbols:
        return 0
    with con:
        cur = con.execute(
            f"DELETE FROM stocks WHERE SYMBOL NOT IN ({','.join('?' * len(symbols))})",
            symbols,
        )
    return cur.rowcount


def fetch_all_rows(con: sqlite3.Connection) -> list[sqlite3.Row]:
    return con.execute("SELECT * FROM stocks").fetchall()
