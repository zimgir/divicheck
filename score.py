
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


def add_score_columns(args, data):

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