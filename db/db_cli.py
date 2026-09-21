"""CLI: rebuild | update [--prune] | stats. Single invocation rebuilds whole DB."""

import argparse
import sqlite3
import sys
from pathlib import Path

from db import DB_DIR, ALL_SYMBOLS_PATH, DIVIDEND_SYMBOLS_PATH
from db.sqldb_controller import SQLDBController

DB_PATH = Path(__file__).resolve().parent / "divicheck.db"

# ponytail: tiny fallback universe, full S&P500 via --symbols sp500 (wikipedia) or file
FALLBACK_SYMBOLS = ["AAPL", "MSFT", "JNJ", "PG", "KO", "PEP", "XOM", "CVX", "T", "VZ"]


def load_symbols(spec: str) -> list[str]:
    spec = (spec or "sp500").strip()
    p = Path(spec)
    if p.is_file():
        return [l.strip().upper() for l in p.read_text().splitlines() if l.strip()]
    if spec.lower() == "sp500":
        try:
            import requests

            html = requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", timeout=30).text
            import re

            syms = re.findall(r'href="/wiki/[^"]*"[^>]*>([A-Z][A-Z0-9.\-]{0,6})<', html)
            seen = [s.replace(".", "-") for s in dict.fromkeys(syms) if 1 <= len(s) <= 6]
            if len(seen) > 400:
                return seen
        except Exception as e:
            print(f"warn: sp500 fetch fail ({e}), fallback list", file=sys.stderr)
        return list(FALLBACK_SYMBOLS)
    return [s.strip().upper() for s in spec.split(",") if s.strip()]


def cmd_rebuild(args) -> int:
    from db.fetcher import fetch_all

    symbols = load_symbols(args.symbols)
    print(f"fetch {len(symbols)} symbols...")
    rows = fetch_all(symbols, sleep=args.sleep)
    db = SQLDBController(args.db)
    con = db.get_connection()
    with con:
        con.execute(db.DROP_TABLE_SQL)
        db.init_db()
        if rows:
            db.upsert_many(rows)
    print(f"rebuild done: {len(rows)}/{len(symbols)} payers stored -> {args.db}")
    return 0


def cmd_update(args) -> int:
    from db.fetcher import fetch_all

    symbols = load_symbols(args.symbols)
    rows = fetch_all(symbols, sleep=args.sleep)
    db = SQLDBController(args.db)
    db.init_db()
    n = db.upsert_many(rows) if rows else 0
    pruned = db.delete_missing(symbols) if args.prune else 0
    print(f"update done: {n} upserted, {pruned} pruned -> {args.db}")
    return 0


def cmd_stats(args) -> int:
    db = SQLDBController(args.db)
    con = db.get_connection()
    try:
        total = con.execute("SELECT COUNT(*) c FROM stocks").fetchone()["c"]
    except sqlite3.OperationalError:
        print("empty DB (no stocks table). run rebuild first.")
        return 1
    print(f"rows: {total}")
    for r in con.execute("SELECT SECTOR, COUNT(*) c FROM stocks GROUP BY SECTOR ORDER BY c DESC"):
        print(f"  {r['SECTOR'] or '?'}: {r['c']}")
    r = con.execute("SELECT AVG(YIELD_1Y) a FROM stocks WHERE YIELD_1Y IS NOT NULL").fetchone()
    print(f"avg yield: {r['a']}")
    print("-- top yield --")
    for x in con.execute("SELECT SYMBOL, YIELD_1Y FROM stocks WHERE YIELD_1Y IS NOT NULL ORDER BY YIELD_1Y DESC LIMIT 10"):
        print(f"  {x['SYMBOL']}: {x['YIELD_1Y']}")
    print("-- top chowder --")
    for x in con.execute("SELECT SYMBOL, CHOWDER FROM stocks WHERE CHOWDER IS NOT NULL ORDER BY CHOWDER DESC LIMIT 10"):
        print(f"  {x['SYMBOL']}: {x['CHOWDER']}")
    return 0


def cmd_symbols(args) -> int:
    from db.fetcher import DBDataFetcher

    if not DB_DIR.exists():
        DB_DIR.mkdir()

    fetcher = DBDataFetcher()
    if not ALL_SYMBOLS_PATH.exists() or args.all:
        symbols = fetcher.fetch_all_symbols(output_path=str(ALL_SYMBOLS_PATH))
        print(f"generated/regenerated {len(symbols)} symbols to {ALL_SYMBOLS_PATH}")
    else:
        symbols = ALL_SYMBOLS_PATH.read_text().splitlines()
        print(f"loaded {len(symbols)} symbols from {ALL_SYMBOLS_PATH}")

    dividend_symbols = fetcher.filter_consecutive_dividend_symbols(symbols, output_path=str(DIVIDEND_SYMBOLS_PATH))
    print(f"saved {len(dividend_symbols)} dividend symbols to {DIVIDEND_SYMBOLS_PATH}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="db_cli")
    ap.add_argument("--db", default=str(DB_PATH))
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("rebuild", "update"):
        p = sub.add_parser(name)
        p.add_argument("--db", default=str(DB_PATH))
        p.add_argument("--symbols", default="sp500", help="sp500 | file.txt | AAPL,MSFT,...")
        p.add_argument("--sleep", type=float, default=1.0)
        if name == "update":
            p.add_argument("--prune", action="store_true")
    sub.add_parser("symbols").add_argument("--all", action="store_true")
    ps = sub.add_parser("stats")
    ps.add_argument("--db", default=str(DB_PATH))
    args = ap.parse_args(argv)
    return {"rebuild": cmd_rebuild, "update": cmd_update, "stats": cmd_stats, "symbols": cmd_symbols}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
