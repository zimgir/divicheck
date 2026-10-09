import pytest
import pandas as pd
from datetime import datetime
from db.fetcher import DBDataFetcher

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
