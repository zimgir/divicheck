import re
import csv

from collections import OrderedDict

import pandas as pd


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


def csv_load_od(path):
    with open(path, newline="", encoding="utf-8-sig") as f:
        return [ OrderedDict(d) for d in csv.DictReader(f) ]


def csv_save_od(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


def csv_load_df(path):
    df = pd.read_csv(path)
    return df


def csv_save_df(path, df):
    df.to_csv(path, index=False)