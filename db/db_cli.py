#!/usr/bin/env python3
"""CLI: update [--prune] [--reset] | stats."""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from db import ALL_SYMBOLS_PATH, DIVIDEND_SYMBOLS_PATH, DB_PATH, FETCH_ROWS_PATH, FALLBACK_SYMBOLS
from db.fetcher import DBDataFetcher
from db.db_controller import SQLDBController



def cmd_symbols(args) -> int:
    fetcher = DBDataFetcher()

    if not ALL_SYMBOLS_PATH.exists() or args.all:
        symbols = fetcher.fetch_all_symbols(output_path=str(ALL_SYMBOLS_PATH))
        print(f"downloaded {len(symbols)} symbols to {ALL_SYMBOLS_PATH}")
    else:
        symbols = ALL_SYMBOLS_PATH.read_text().splitlines()
        print(f"loaded {len(symbols)} symbols from {ALL_SYMBOLS_PATH}")

    dividend_symbols = fetcher.filter_dividend_symbols(symbols, sleep=args.sleep, output_path=args.symbols)

    print(f"saved {len(dividend_symbols)} dividend symbols to {args.symbols}")

    return 0


def load_symbols(args):
    if args.symbols.exists():
        return args.symbols.read_text().splitlines()

    try:
        cmd_symbols(args)
        if args.symbols.exists():
            return args.symbols.read_text().splitlines()
    except Exception as e:
        print(f"Error generating symbols: {e}")

    return list(FALLBACK_SYMBOLS)


def cmd_update(args) -> int:
    symbols = load_symbols(args)

    fetcher = DBDataFetcher()
    fetcher.fetch_db_rows(symbols, FETCH_ROWS_PATH, sleep=args.sleep)

    db = SQLDBController(args.db)

    if args.reset:
        db.reset_db()
    else:
        db.init_db()

    n = db.upsert_from_csv(FETCH_ROWS_PATH)

    pruned = 0
    if args.prune:
        pruned = db.delete_missing(symbols)

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


def main(argv=None) -> int:
    parser_main = argparse.ArgumentParser(
        prog="db_cli",
        description="Database CLI tools.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser_main.add_argument("--db", default=str(DB_PATH), help="Path to database file.")
    parser_main.add_argument("--symbols", type=Path, default=DIVIDEND_SYMBOLS_PATH, help="Path to symbols file (used by symbols/update).")
    parser_main.add_argument("--sleep", type=float, default=1.0, help="Sleep time between fetches (used by symbols/update).")
    parser_main.add_argument("--batch", type=int, default=40, help="Batch size for fetches (used by symbols/update).")

    parser_sub = parser_main.add_subparsers(dest="cmd", required=True)

    parser_symbols = parser_sub.add_parser("symbols", help="Generate/update symbol lists.")
    parser_symbols.add_argument("--all", action="store_true", help="Force regenerate all symbols.")

    parser_update = parser_sub.add_parser("update", help="Update database.")
    parser_update.add_argument("--prune", action="store_true", help="Remove symbols not in the list.")
    parser_update.add_argument("--reset", action="store_true", help="Rebuild database from scratch.")

    parser_stats = parser_sub.add_parser("stats", help="Show database statistics.")

    args = parser_main.parse_args(argv)

    cmds = {"symbols": cmd_symbols,
            "update": cmd_update,
            "stats": cmd_stats,
            }

    return cmds[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
