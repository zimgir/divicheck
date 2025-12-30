#!/usr/bin/env python3

import re
import sys
import csv
import json
import argparse

from collections import defaultdict, OrderedDict
from statistics import mean

from pprint import pprint

# ----------------------------
# Column explanations
# ----------------------------
COL_DESC = {
    "Price": "Current stock price.",
    "Div Yield": "Annual dividend yield percentage. Higher is better for income investors.",
    "5Y Avg Yield": "Average dividend yield over last 5 years.",
    "Current Div": "Most recent dividend payment.",
    "Payouts/Year": "Number of dividend payments per year.",
    "Annualized": "Annualized dividend amount.",
    "Low": "52-week low price.",
    "High": "52-week high price.",
    "Chowder Number": "Dividend Yield + Dividend Growth Rate. Measures income + growth.",
    "DGR 1Y": "Dividend Growth Rate over 1 year.",
    "DGR 3Y": "Dividend Growth Rate over 3 years.",
    "DGR 5Y": "Dividend Growth Rate over 5 years.",
    "DGR 10Y": "Dividend Growth Rate over 10 years.",
    "TTR 1Y": "Total return over 1 year.",
    "TTR 3Y": "Total return over 3 years.",
    "FV (Peter Lynch)": "Fair value estimate using Peter Lynch method.",
    "FV (Peter Lynch) %": "Percent over/undervalued relative to fair value.",
    "EPS 1Y": "Earnings per share growth (1 year).",
    "Revenue 1Y": "Revenue growth over last year.",
    "NPM": "Net profit margin. Measures profitability.",
    "CF/Share": "Cash flow per share.",
    "ROE": "Return on equity. Capital efficiency.",
    "Current R": "Current ratio. Liquidity measure.",
    "Debt/Capital": "Debt to total capital. Lower is safer.",
    "ROTC": "Return on total capital.",
    "P/E": "Price-to-earnings ratio. Valuation metric.",
    "P/BV": "Price-to-book value ratio.",
    "PEG": "Price / Earnings to Growth ratio. Valuation adjusted for growth."
}

COL_LOWER_IS_BETTER = {
    "Debt/Capital",
    "P/E",
    "PEG",
    "P/BV"
}

COL_SECTOR = "Sector"

COL_FAIR_VALUE_PCT = "FV (Peter Lynch) %"

COL_ANNUAL_YIELD = "Annualized"
COL_ANNUAL_EPS = "EPS 1Y"

COL_SAFETY_SCORE_INPUTS = {
    COL_ANNUAL_EPS,
    "Debt/Capital",
    "ROE",
    "CF/Share",
}

# ----------------------------
# Utilities
# ----------------------------
pattern_dollar_sign = re.compile(r"\$")
pattern_percent_sign = re.compile(r"%")
pattern_times_sign = re.compile(r"x")

def to_float(value):
    try:
    
        value = re.sub(pattern_dollar_sign,"",value)
        value = re.sub(pattern_percent_sign,"",value)
        value = re.sub(pattern_times_sign,"",value)

        if value is None or value == "":
            return None
        return float(value)
    except (ValueError, TypeError):
        return None


def load_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [ OrderedDict(d) for d in csv.DictReader(f) ]


def save_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# ----------------------------
# Threshold generation
# ----------------------------
def generate_thresholds(rows, output_path):
    columns = rows[0].keys()
    numeric_columns = defaultdict(list)

    for row in rows:
        for col in columns:
            v = to_float(row[col])
            if v is not None:
                numeric_columns[col].append(v)

    thresholds = {}
    for col, values in numeric_columns.items():
        if not values:
            continue
        thresholds[col] = {
            "min": min(values),
            "max": max(values),
            "avg": mean(values),
            "desc": COL_DESC.get(col, "No description available.")
        }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(thresholds, f, indent=2)

    print(f"Thresholds JSON written to {output_path}")


# ----------------------------
# Filtering
# ----------------------------
def load_thresholds(args):
    if not args.thresholds:
        raise Exception("filtering requires --thresholds - Use -g to generate initial passthrough thresholds")

    with open(args.thresholds, "r") as f:
        thresholds = json.load(f)

    return thresholds

def update_reject_stats(reject_stats, col, limit):
    if reject_stats is None:
        return
    
    reject_name = f"{col}_{limit}"
    reject_count = reject_stats.get(reject_name, 0)
    reject_count += 1
    reject_stats[reject_name] = reject_count

def row_passes_thresholds(row, thresholds, reject_stats=None):
    for col, limits in thresholds.items():

        v = to_float(row.get(col))

        if v is None:
            continue # skip non numeric values for filtering

        min_thresh = limits.get("min", None)

        if min_thresh and v < min_thresh:
            update_reject_stats(reject_stats, col, "min")
            return False
        
        max_thresh = limits.get("max", None)
        
        if max_thresh and v > max_thresh:
            update_reject_stats(reject_stats, col, "min")
            return False

    return True


def filter_initial(args, rows):

    thresholds = load_thresholds(args)

    filtered = []
    reject_stats = OrderedDict()

    print(f"\nGot {len(rows)} rows before filtering\n")

    for r in rows:
        if row_passes_thresholds(r, thresholds, reject_stats):
            filtered.append(r)

    reject_stats = OrderedDict(sorted(reject_stats.items(),key=lambda x: x[1], reverse=True))
    print("\nFilter reject stats:\n")
    pprint(reject_stats)

    print(f"\nGot {len(filtered)} rows after initial filtering\n")

    return filtered


# ----------------------------
# Scoring
# ----------------------------
DEFAULT_SCORE_WEIGHTS = {
    "columns": {
        "Div Yield": 1.2,
        "Chowder Number": 1.5,
        "DGR 5Y": 1.2,
        "DGR 10Y": 1.0,
        "EPS 1Y": 1.0,
        "Revenue 1Y": 0.8,
        "ROE": 1.0,
        "ROTC": 0.8,
        "TTR 3Y": 1.0,
        # penalties (lower is better)
        "Debt/Capital": -1.2,
        "P/E": -0.8,
        "PEG": -0.6,
    },

    # derrived scores
    "safety" : 1.2,
    "value": 0.8,
}

COL_TOTAL_SCORE = "_total_score"
COL_SAFETY_SCORE = "_safety_score"
COL_VALUE_SCORE = "_value_score"
COL_PAYOUT_RATIO = "_payout_ratio"

def load_weights(args):
    if args.weights:
        with open(args.weights, "r") as f:
            weights = json.load(f)
    else:
        weights = DEFAULT_SCORE_WEIGHTS

    return weights


def sector_min_max(rows, column):
    data = defaultdict(list)
    for r in rows:
        v = to_float(r.get(column))
        if v is not None:
            data[r[COL_SECTOR]].append(v)

    return {
        sector : (min(vals), max(vals))
        for sector, vals in data.items() if vals
    }


def sector_normalize(value, sector, min_max):
    mn, mx = min_max.get(sector, (None, None))
    if mn is None or mx is None or mx == mn:
        return 0.5
    return (value - mn) / (mx - mn)


def compute_value_score(row):
    fv = to_float(row.get(COL_FAIR_VALUE_PCT))
    if fv is None:
        return 0.5

    # clamp to [-50%, +50%]
    fv = max(-50.0, min(50.0, fv))
    return (1.0 - (fv + 50.0) / 100.0)


def compute_safety_score(row, sector_stats):
    scores = []

    # Derived payout ratio proxy
    div = to_float(row.get(COL_ANNUAL_YIELD))
    eps = to_float(row.get(COL_ANNUAL_EPS))

    if div is not None and eps is not None and eps > 0:
        payout = div / eps
        scores.append(1.0 - min(payout, 1.5) / 1.5)
    else:
        payout = 0.0

    row[COL_PAYOUT_RATIO] = payout

    for col in COL_SAFETY_SCORE_INPUTS:
        v = to_float(row.get(col))
        if v is None:
            continue
        norm = sector_normalize(v, row[COL_SECTOR], sector_stats[col])
        if col in COL_LOWER_IS_BETTER:
            norm = 1.0 - norm
        scores.append(norm)

    return sum(scores) / len(scores) if scores else 0.5


def compute_scores(args, rows):

    weights = load_weights(args)

    col_weights = weights.get("columns", {})
    value_weight = weights.get("value", 0.0)
    safety_weight = weights.get("safety", 0.0)

    sector_stats = {
        col: sector_min_max(rows, col)
        for col in col_weights
    }

    safety_stats = {
        col: sector_min_max(rows, col)
        for col in COL_SAFETY_SCORE_INPUTS
    }

    scored = []

    for row in rows:
        total = 0.0
        wsum = 0.0

        for col, w in col_weights.items():
            v = to_float(row.get(col))
            if v is None:
                continue

            norm = sector_normalize(v, row[COL_SECTOR], sector_stats[col])

            if col in COL_LOWER_IS_BETTER:
                norm = 1.0 - norm

            total += norm * abs(w)
            wsum += abs(w)

        # valuation bonus
        value_score = compute_value_score(row)
        total += value_score * value_weight
        wsum += value_weight

        row[COL_VALUE_SCORE] = value_score
        row.move_to_end(COL_VALUE_SCORE, last=False)

        # safety proxy
        safety_score = compute_safety_score(row, safety_stats)
        total += safety_score * safety_weight
        wsum += safety_weight

        row[COL_SAFETY_SCORE] = safety_score
        row.move_to_end(COL_SAFETY_SCORE, last=False)

        row[COL_TOTAL_SCORE] = total # / wsum if wsum else 0.0 # add this if want normalized score
        row.move_to_end(COL_TOTAL_SCORE, last=False)

        scored.append(row)

    return scored


# ----------------------------
# Main
# ----------------------------
def divicheck(args):

    rows = load_csv(args.input)

    if args.generate_thresholds:
        generate_thresholds(rows, args.thresholds)
        return

    filtered = filter_initial(args, rows)

    scored = compute_scores(args, filtered)

    # TODO: add additional computed score filters
    filtered_scored = scored

    if len(filtered_scored) == 0:
        print(f"\nNo data for output CSV after filtering :(\n")
        return

    filtered_scored.sort(key=lambda r: (r[COL_SECTOR], -r["_total_score"]))

    save_csv(args.output, filtered_scored)

    print(f"\nFiltered CSV written to {args.output}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", default=None, help="Input all divident stocks CSV file from: https://www.dripinvesting.org")
    parser.add_argument("-o", "--output", default="_divident_stocks_filtered.csv", help="Filtered output CSV")
    parser.add_argument("-t", "--thresholds", default="_divident_stocks_thresholds.json", help="Thresholds JSON for filtering")
    parser.add_argument("-g", "--generate_thresholds", action="store_true", help="Generate initial thresholds JSON and exit")
    parser.add_argument("-w", "--weights", help="Score weights JSON")

    args = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
        # for quick and dirty hardcoded debug
        args.input = "stocks-2025-12-26.csv"
        args.thresholds = "_divident_stocks_thresholds.json"


    divicheck(args)