"""Stats + verification. Run: python tests/test_db.py [db_path]. No pytest needed."""

import sqlite3
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.connection import get_connection, init_db  # noqa: E402
from db.repository import upsert_many  # noqa: E402

FIXTURES = [
    {"SYMBOL": "AAA", "COMPANY": "A Co", "SECTOR": "Energy", "YIELD_1Y": 0.05, "DGR_5Y": 0.07,
     "CHOWDER": 0.12, "CUR_DIV": 2.0, "P_E": 12.0, "P_BV": 1.5, "UPDATED_AT": "2026-01-01T00:00:00+00:00"},
    {"SYMBOL": "BBB", "COMPANY": "B Co", "SECTOR": "Energy", "YIELD_1Y": 0.03, "DGR_5Y": 0.04,
     "CHOWDER": 0.07, "CUR_DIV": 1.0, "P_E": 20.0, "P_BV": 2.5, "UPDATED_AT": "2026-01-01T00:00:00+00:00"},
]


def populate(con: sqlite3.Connection) -> None:
    init_db(con)
    upsert_many(con, FIXTURES)


def verify(con: sqlite3.Connection) -> list[str]:
    errs = []
    rows = con.execute("SELECT * FROM stocks").fetchall()
    if not rows:
        return ["empty table"]
    syms = [r["SYMBOL"] for r in rows]
    if any(s is None for s in syms):
        errs.append("null SYMBOL found")
    if len(set(syms)) != len(syms):
        errs.append("duplicate SYMBOLs")
    for r in rows:
        if r["CUR_DIV"] is not None and not r["CUR_DIV"] > 0:
            errs.append(f"{r['SYMBOL']}: non-payer CUR_DIV={r['CUR_DIV']}")
        y = r["YIELD_1Y"]
        if y is not None and not 0 <= y <= 1:
            errs.append(f"{r['SYMBOL']}: yield out of range {y}")
        for c in ("P_E", "P_BV"):
            v = r[c]
            if v is not None and not v > 0:
                errs.append(f"{r['SYMBOL']}: {c}<=0 ({v})")
        if all(r[c] is not None for c in ("CHOWDER", "YIELD_1Y", "DGR_5Y")):
            if abs(r["CHOWDER"] - (r["YIELD_1Y"] + r["DGR_5Y"])) > 1e-6:
                errs.append(f"{r['SYMBOL']}: CHOWDER != YIELD+DGR_5Y")
    return errs


def stats(con: sqlite3.Connection) -> None:
    total = con.execute("SELECT COUNT(*) c FROM stocks").fetchone()["c"]
    print(f"rows: {total}")
    for r in con.execute("SELECT SECTOR, COUNT(*) c FROM stocks GROUP BY SECTOR ORDER BY c DESC"):
        print(f"  {r['SECTOR'] or '?'}: {r['c']}")
    ys = [r[0] for r in con.execute("SELECT YIELD_1Y FROM stocks WHERE YIELD_1Y IS NOT NULL")]
    if ys:
        print(f"avg yield: {statistics.mean(ys):.4f} median: {statistics.median(ys):.4f}")
    print("-- top yield --")
    for r in con.execute("SELECT SYMBOL, YIELD_1Y FROM stocks WHERE YIELD_1Y IS NOT NULL ORDER BY YIELD_1Y DESC LIMIT 10"):
        print(f"  {r['SYMBOL']}: {r['YIELD_1Y']}")
    print("-- top chowder --")
    for r in con.execute("SELECT SYMBOL, CHOWDER FROM stocks WHERE CHOWDER IS NOT NULL ORDER BY CHOWDER DESC LIMIT 10"):
        print(f"  {r['SYMBOL']}: {r['CHOWDER']}")


def selftest() -> int:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    populate(con)
    errs = verify(con)
    stats(con)
    if errs:
        print("FAIL:", *errs, sep="\n  ")
        return 1
    # pure calc checks
    from db.fetcher import cagr, calc_chowder, calc_peg

    assert abs(cagr(1, 2, 1) - 1.0) < 1e-9
    assert cagr(0, 1, 1) is None
    assert abs(calc_chowder(0.05, 0.07) - 0.12) < 1e-9
    assert calc_peg(20, -0.1) is None
    print("selftest OK")
    return 0


def main() -> int:
    if len(sys.argv) > 1:
        con = get_connection(sys.argv[1])
        try:
            stats(con)
            errs = verify(con)
        except sqlite3.OperationalError as e:
            print(f"verify fail: {e}")
            return 1
        if errs:
            print("FAIL:", *errs, sep="\n  ")
            return 1
        print("verify OK")
        return 0
    return selftest()


if __name__ == "__main__":
    raise SystemExit(main())
