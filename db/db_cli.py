#!/usr/bin/env python3
"""CLI: update [--prune] [--reset] | stats."""

import sys
import argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


from db import ALL_SYMBOLS_PATH, DIVIDEND_SYMBOLS_PATH, DEFAULT_SYMBOLS_PATH, DB_PATH, FETCH_ROWS_PATH, FALLBACK_SYMBOLS
from db.fetcher import DBDataFetcher
from db.db_controller import SQLDBController
from db.logger import DBLogger, log_streams_to



def cmd_symbols(args) -> int:
    fetcher = DBDataFetcher()

    if not ALL_SYMBOLS_PATH.exists() or args.all:
        symbols = fetcher.fetch_all_symbols(output_path=str(ALL_SYMBOLS_PATH))
        print(f"downloaded {len(symbols)} symbols to {ALL_SYMBOLS_PATH}")
    else:
        symbols = ALL_SYMBOLS_PATH.read_text().splitlines()
        print(f"loaded {len(symbols)} symbols from {ALL_SYMBOLS_PATH}")

    dividend_symbols = fetcher.fetch_divident_symbols(symbols, sleep=args.sleep, output_path=args.symbols)

    print(f"saved {len(dividend_symbols)} dividend symbols to {args.symbols}")

    return 0


def load_symbols(args):
    default_symbols = []
    if DEFAULT_SYMBOLS_PATH.exists():
        default_symbols = DEFAULT_SYMBOLS_PATH.read_text().splitlines()

    dividend_symbols = []
    if args.symbols.exists():
        dividend_symbols = args.symbols.read_text().splitlines()
    else:
        try:
            cmd_symbols(args)
            if args.symbols.exists():
                dividend_symbols = args.symbols.read_text().splitlines()
        except Exception as e:
            print(f"Error generating symbols: {e}")

    if not dividend_symbols and not default_symbols:
        dividend_symbols = list(FALLBACK_SYMBOLS)

    return list(dict.fromkeys(default_symbols + dividend_symbols))


def cmd_update(args) -> int:
    symbols = load_symbols(args)

    fetcher = DBDataFetcher()
    fetcher.fetch_db_rows(symbols, FETCH_ROWS_PATH, sleep=args.sleep)

    db = SQLDBController(args.db)

    if args.reset:
        db.reset_db()
    else:
        db.init_db()

    DBLogger.print_progress(0, 100, "Writing to database")
    n = db.upsert_from_csv(FETCH_ROWS_PATH)
    DBLogger.print_progress(100, 100, "Writing to database")

    pruned = 0
    if args.prune:
        pruned = db.delete_missing(symbols)

    print(f"update done: {n} upserted, {pruned} pruned -> {args.db}")

    return 0


def cmd_stats(args) -> int:
    db_path = Path(args.db)
    file_size = db_path.stat().st_size if db_path.exists() else 0

    total_rows = 0
    matching_rows_data = []
    source = "FALLBACK_SYMBOLS"
    symbols = list(FALLBACK_SYMBOLS)

    if DEFAULT_SYMBOLS_PATH.exists():
        symbols = DEFAULT_SYMBOLS_PATH.read_text().splitlines()
        source = "DEFAULT_SYMBOLS"

    db = SQLDBController(args.db)
    con = db.get_connection()
    try:
        cur = con.execute("SELECT count(*) FROM stocks")
        total_rows = cur.fetchone()[0]

        if symbols:
            placeholders = ",".join(["?"] * len(symbols))
            cur = con.execute(f"SELECT SYMBOL, COMPANY, PRICE, YIELD_1Y, CHOWDER, UPDATED_AT FROM stocks WHERE SYMBOL IN ({placeholders})", symbols)
            matching_rows_data = cur.fetchall()
    except Exception:
        pass

    if getattr(args, 'json', False):
        import json
        out = {
            "db_path": str(db_path),
            "file_size": file_size,
            "total_rows": total_rows,
            "source": source,
            "symbols": symbols,
            "rows": [
                {
                    "SYMBOL": r['SYMBOL'],
                    "COMPANY": r['COMPANY'],
                    "PRICE": r['PRICE'],
                    "YIELD_1Y": r['YIELD_1Y'],
                    "CHOWDER": r['CHOWDER'],
                    "UPDATED_AT": r['UPDATED_AT']
                } for r in matching_rows_data
            ]
        }
        print(json.dumps(out))
        return 0

    print(f"\n")

    print(f"Database: {db_path}")
    print(f"File size: {file_size} bytes")
    print(f"Total rows: {total_rows}")
    print(f"Matching rows ({source}): {len(matching_rows_data)}")

    if matching_rows_data:
        print("\nMatching symbols:\n")
        header = f"  {'SYMBOL':<6} | {'COMPANY':<30} | {'PRICE':<8} | {'YIELD 1Y':<9} | {'CHOWDER':<9} | {'UPDATED AT'}"
        print(header)
        print("  " + "-" * (len(header) - 2))
        for r in matching_rows_data:
            symbol = str(r['SYMBOL'] or '')
            company = str(r['COMPANY'] or '')[:30]
            price = f"{r['PRICE']:.2f}" if r['PRICE'] is not None else ""
            yield_1y = f"{r['YIELD_1Y']:.2f}%" if r['YIELD_1Y'] is not None else ""
            chowder = f"{r['CHOWDER']:.2f}%" if r['CHOWDER'] is not None else ""
            updated_at = str(r['UPDATED_AT'] or '')
            print(f"  {symbol:<6} | {company:<30} | {price:<8} | {yield_1y:<9} | {chowder:<9} | {updated_at}")

    print(f"\n")

    return 0


def main(argv=None) -> int:
    logger = DBLogger.get_logger("db_cli")
    cmdline = sys.argv if argv is None else [sys.argv[0], *argv]
    logger.info("command: " + " ".join(str(a) for a in cmdline))
    with log_streams_to(logger):
        parser_main = argparse.ArgumentParser(
            prog="db_cli",
            description="Database CLI tools.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser_main.add_argument("--db", default=str(DB_PATH), help="Path to database file.")
        parser_main.add_argument("--symbols", type=Path, default=DIVIDEND_SYMBOLS_PATH, help="Path to symbols file (used by symbols/update).")
        parser_main.add_argument("--sleep", type=float, default=1.0, help="Sleep time between fetches (used by symbols/update).")
        parser_main.add_argument("--batch", type=int, default=40, help="Batch size for fetches (used by symbols/update).")
        parser_main.add_argument("--progress", type=Path, default=None, help="Path to JSON progress file (used by symbols/update).")

        parser_sub = parser_main.add_subparsers(dest="cmd", required=True)

        parser_symbols = parser_sub.add_parser("symbols", help="Generate/update symbol lists.")
        parser_symbols.add_argument("--all", action="store_true", help="Force regenerate all symbols.")

        parser_update = parser_sub.add_parser("update", help="Update database.")
        parser_update.add_argument("--prune", action="store_true", help="Remove symbols not in the list.")
        parser_update.add_argument("--reset", action="store_true", help="Rebuild database from scratch.")

        parser_stats = parser_sub.add_parser("stats", help="Show database statistics.")
        parser_stats.add_argument("--json", action="store_true", help="Output stats as JSON.")

        args = parser_main.parse_args(argv)

        DBLogger.progress_path = args.progress

        cmds = {"symbols": cmd_symbols,
                "update": cmd_update,
                "stats": cmd_stats,
                }

        return cmds[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
