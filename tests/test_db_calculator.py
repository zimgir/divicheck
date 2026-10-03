import pytest
import pandas as pd
from pathlib import Path
from db.calculator import DBRowCalculator
import json
import functools

@functools.lru_cache(maxsize=1)
def _get_jnj_data():
    with open(Path(__file__).parent / "jnj_raw.json", "r") as f:
        d = json.load(f)
    divs_data = d.get("dividends")
    divs = pd.Series(divs_data["values"], index=pd.to_datetime(divs_data["index"], utc=True)) if divs_data else None

    def mk_df(obj, is_history=False):
        if obj is None: return None
        idx = pd.to_datetime(obj["index"], utc=True) if is_history else obj["index"]
        cols = []
        for c in obj["columns"]:
            try:
                cols.append(pd.to_datetime(c))
            except:
                cols.append(c)
        return pd.DataFrame(obj["data"], index=idx, columns=cols)

    return {
        "info": d["info"],
        "dividends": divs,
        "income_stmt": mk_df(d["income_stmt"]),
        "balance_sheet": mk_df(d["balance_sheet"]),
        "cashflow": mk_df(d["cashflow"]),
        "history": mk_df(d["history"], is_history=True),
    }

@pytest.fixture
def jnj_data():
    return _get_jnj_data()


def test_calculator_basic(jnj_data):
    calc = DBRowCalculator("JNJ", jnj_data)
    res = calc.calculate()

    assert res["SYMBOL"] == "JNJ"
    assert res["SECTOR"] == "Healthcare"
    assert res["PRICE"] == 264.89
    assert res["COMPANY"] == "Johnson & Johnson"
    assert res["INDUSTRY"] == "Drug Manufacturers - General"
    assert res["CUR_DIV"] is not None
    assert isinstance(res["UPDATED_AT"], str)


def test_safe_division():
    calc = DBRowCalculator("TEST", {})
    assert calc._safe_division(10, 2) == 5.0
    assert calc._safe_division(10, 0) is None
    assert calc._safe_division(None, 2) is None
    assert calc._safe_division(10, None) is None
    assert calc._safe_division("abc", 2) is None


def test_extract_financial_cell():
    calc = DBRowCalculator("TEST", {})
    df = pd.DataFrame({"col": [100.0]}, index=["Total Revenue"])
    assert calc._extract_financial_cell(df, ["Total Revenue"]) == 100.0
    assert calc._extract_financial_cell(df, ["NonExistent"]) is None
    assert calc._extract_financial_cell(None, ["Total Revenue"]) is None


def test_compound_annual_growth_rate():
    calc = DBRowCalculator("TEST", {})
    cagr = calc._calculate_compound_annual_growth_rate(100.0, 121.0, 2)
    assert pytest.approx(cagr, 0.001) == 0.10
    assert calc._calculate_compound_annual_growth_rate(0, 100, 1) is None
    assert calc._calculate_compound_annual_growth_rate(100, 100, 0) is None


def test_dividend_growth_rate():
    calc = DBRowCalculator("TEST", {})
    dates = pd.date_range(start="2015-01-01", end="2025-01-01", freq="YE")
    s = pd.Series([1.0] * len(dates), index=dates)
    dgr = calc._calculate_dividend_growth_rate(s, 3)
    assert dgr == 0.0
    assert calc._calculate_dividend_growth_rate(None, 3) is None


def test_peter_lynch_fair_price():
    calc = DBRowCalculator("TEST", {})
    info = {"trailingEps": 4.0}
    income = pd.DataFrame({
        "2020": [100.0],
        "2021": [110.0],
        "2022": [121.0],
    }, index=["Net Income"])
    fp = calc._calculate_peter_lynch_fair_price(info, income)
    assert fp is not None


def test_normalize_five_year_dividend_yield():
    calc = DBRowCalculator("TEST", {})
    assert calc._normalize_five_year_dividend_yield(2.5, 1.0, 50.0) == 0.025
    assert calc._normalize_five_year_dividend_yield(None, 1.0, 50.0) is None


def test_ttr_edge_cases():
    calc = DBRowCalculator("TEST", {"history": pd.DataFrame()})
    t1, t3 = calc._calculate_ttr()
    assert t1 is None
    assert t3 is None


def test_empty_or_malformed_data():
    calc = DBRowCalculator("EMPTY", {})
    res = calc.calculate()
    assert res["SYMBOL"] == "EMPTY"
    assert res["PRICE"] is None
    assert res["YIELD_1Y"] is None
    assert res["CHOWDER"] is None


def test_rotc_fallback():
    calc = DBRowCalculator("TEST1", {
        "income_stmt": pd.DataFrame({"2023": [100.0]}, index=["EBIT"]),
        "balance_sheet": pd.DataFrame({"2023": [200.0, 300.0]}, index=["Total Debt", "Total Stockholder Equity"])
    })
    assert calc._calc_rotc() == 100.0 / (200.0 + 300.0)


def test_debt_capital_fallback():
    calc = DBRowCalculator("TEST2", {
        "info": {"debtToEquity": 100.0}
    })
    assert calc._calc_debt_capital() == 50.0


def test_peg_fallback():
    calc = DBRowCalculator("TEST3", {
        "info": {"trailingPE": 20.0, "earningsGrowth": 0.10}
    })
    assert calc._calc_peg() == 20.0 / (0.10 * 100)


def test_jnj_reference_row(jnj_data):
    calc = DBRowCalculator("JNJ", jnj_data)
    processed = calc.calculate()

    expected = {
        "SYMBOL": "JNJ", "SECTOR": "Healthcare", "PRICE": 264.89, "FAIR_VALUE": 2.1473,
        "YIELD_1Y": 2.0, "YIELD_5Y": 2.75, "TTR_1Y": 45.7118, "TTR_3Y": 21.7583,
        "DGR_1Y": 4.6843, "DGR_3Y": 4.9223, "DGR_5Y": 5.2485, "DGR_10Y": 5.7095,
        "CHOWDER": 7.2485, "ROE": 25.742, "NPM": 21.482, "ROTC": 17.6422,
        "CUR_R": 1.0277, "EPS_1Y": -0.9, "CF_SHARE": 10.1789, "PAYOUT_RATIO": 0.6079,
        "DEBT_CAPITAL": 37.0205, "NET_WORTH": 81544000000.0, "REVENUE_1Y": 6.6, "PEG": 2.81, "P_E": 30.716,
        "P_BV": 7.5082, "FAIR_PRICE": 123.428, "PRICE_LOW": 182.94, "PRICE_HIGH": 281.07,
        "CUR_DIV": 1.34, "PREV_DIV": 1.34, "NUM_DIV_1Y": 4, "DIV_1Y": 5.28,
        "COMPANY": "Johnson & Johnson", "INDUSTRY": "Drug Manufacturers - General"
    }

    for k, expected_val in expected.items():
        actual_val = processed[k]
        if isinstance(expected_val, float):
            assert actual_val == pytest.approx(expected_val, rel=1e-3), f"Mismatch on {k}: expected {expected_val}, got {actual_val}"
        else:
            assert actual_val == expected_val, f"Mismatch on {k}: expected {expected_val}, got {actual_val}"

    assert isinstance(processed["PAY_DATE"], str)
    assert isinstance(processed["EX_DATE"], str)


def test_variable_div_1y():
    now = pd.Timestamp.now()
    dates = [now - pd.Timedelta(days=30), now - pd.Timedelta(days=120), now - pd.Timedelta(days=210), now - pd.Timedelta(days=300)]
    divs = pd.Series([1.5, 1.2, 1.2, 1.0], index=dates)
    calc = DBRowCalculator("TEST", {"dividends": divs})
    res = calc.calculate()
    assert res["DIV_1Y"] == 4.9

