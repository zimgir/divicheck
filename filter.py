-
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


def filter_with_thresholds(args, rows):

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
