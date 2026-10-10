import pytest
import pandas as pd
from datetime import datetime
from db.fetcher import DBDataFetcher
from db.tests.test_db_calculator import _get_jnj_data

def test_fetch_db_rows_flushes_per_symbol(tmp_path):
    fetcher = DBDataFetcher()
    data = _get_jnj_data()
    fetcher._fetch_raw_data = lambda sym: data if sym == "JNJ" else None
    out = tmp_path / "rows.csv"

    fetcher.fetch_db_rows(["JNJ", "MISSING"], out, sleep=0)

    df = pd.read_csv(out)
    assert len(df) == 1
    assert df.iloc[0]["SYMBOL"] == "JNJ"
    assert out.read_text().count("SYMBOL") == 1


def test_fetch_db_rows_no_rows_creates_no_file(tmp_path):
    fetcher = DBDataFetcher()
    fetcher._fetch_raw_data = lambda sym: None
    out = tmp_path / "rows.csv"

    fetcher.fetch_db_rows(["A", "B"], out, sleep=0)

    assert not out.exists()


def test_filter_divident_symbols_logic():
    fetcher = DBDataFetcher()
    current_year = datetime.now().year
    cy = current_year
    dates = pd.to_datetime([f"{cy-3}-03-01", f"{cy-2}-03-01", f"{cy-1}-03-01"])

    # Strictly increasing: 1.0 -> 2.0 -> 3.0
    inc_series = pd.Series([1.0, 2.0, 3.0], index=dates)
    # Flat / stayed same: 1.0 -> 2.0 -> 2.0 (should fail strictly increasing)
    flat_series = pd.Series([1.0, 2.0, 2.0], index=dates)
    # Decreasing: 3.0 -> 2.0 -> 1.0
    dec_series = pd.Series([3.0, 2.0, 1.0], index=dates)

    assert fetcher._filter_divident_symbols(inc_series, last_n_years=3) is True
    assert fetcher._filter_divident_symbols(flat_series, last_n_years=3) is False
    assert fetcher._filter_divident_symbols(dec_series, last_n_years=3) is False
