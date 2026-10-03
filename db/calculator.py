import pandas as pd
from datetime import datetime, timezone

from db.schema import SCHEMA, format_date

class DBRowCalculator:
    """Calculates financial metrics and row data for a given stock symbol based on fetched raw data."""
    def __init__(self, symbol: str, data: dict):
        self.symbol = symbol
        self.financial_data = data

        self.company_info = self.financial_data.get("info", {})
        self.dividend_series = self.financial_data.get("dividends")
        self.income_statement = self.financial_data.get("income_stmt")
        self.balance_sheet = self.financial_data.get("balance_sheet")
        self.cash_flow = self.financial_data.get("cashflow")
        self.history = self.financial_data.get("history")
        self.ttr_1y, self.ttr_3y = self._calculate_ttr()

        self.current_price = self.company_info.get("currentPrice") or self.company_info.get("regularMarketPrice")

        # Parse dividend attributes
        try:
            dividend_dataframe = pd.Series(self.dividend_series) if self.dividend_series is not None else pd.Series(dtype=float)
            self.dividends_last_twelve_months = None
            if not dividend_dataframe.empty:
                dividend_dataframe.index = pd.to_datetime(dividend_dataframe.index)
                naive_index = dividend_dataframe.index.tz_convert(None) if dividend_dataframe.index.tz is not None else dividend_dataframe.index
                self.dividends_last_twelve_months = dividend_dataframe[naive_index >= (pd.Timestamp.now() - pd.Timedelta(days=365))]
                self.dividend_count_last_year = int(len(self.dividends_last_twelve_months)) if len(self.dividends_last_twelve_months) else 0
                self.current_dividend = float(dividend_dataframe.iloc[-1]) if len(dividend_dataframe) else None
            else:
                self.dividend_count_last_year = 0
                self.current_dividend = float(self.company_info.get("dividendRate") or 0) or None
        except Exception:
            self.current_dividend, self.dividend_count_last_year = None, 0
            self.dividends_last_twelve_months = None

        self.current_dividend = self.current_dividend or float(self.company_info.get("trailingAnnualDividendRate") or 0) or None

        try:
            self.payment_date = format_date(self.dividend_series.index[-1]) if self.dividend_series is not None and len(self.dividend_series) else None
            self.previous_dividend = float(self.dividend_series.iloc[-2]) if self.dividend_series is not None and len(self.dividend_series) > 1 else None
        except Exception:
            self.payment_date, self.previous_dividend = None, None

        try:
            ex_dividend_timestamp = self.company_info.get("exDividendDate")
            self.ex_dividend_date = format_date(datetime.fromtimestamp(int(ex_dividend_timestamp), tz=timezone.utc)) if ex_dividend_timestamp else self.payment_date
        except Exception:
            self.ex_dividend_date = self.payment_date

        self.dividend_growth_rates = {n: self._calculate_dividend_growth_rate(self.dividend_series, n) for n in (1, 3, 5, 10)}

        # Financial statement metrics
        self.total_revenue = self._extract_financial_cell(self.income_statement, ["Total Revenue"])
        self.net_income = self._extract_financial_cell(self.income_statement, ["Net Income"])
        self.ebit_earnings = self._extract_financial_cell(self.income_statement, ["EBIT"])
        self.operating_income = self._extract_financial_cell(self.income_statement, ["Operating Income", "EBIT"])
        self.total_debt = self._extract_financial_cell(self.balance_sheet, ["Total Debt"])
        self.total_equity = self._extract_financial_cell(self.balance_sheet, ["Total Stockholder Equity", "Total Equity", "Stockholders Equity", "Common Stock Equity", "Total Equity Gross Minority Interest"])
        self.current_assets = self._extract_financial_cell(self.balance_sheet, ["Total Current Assets", "Current Assets"])
        self.current_liabilities = self._extract_financial_cell(self.balance_sheet, ["Total Current Liabilities", "Current Liabilities"])
        self.total_assets = self._extract_financial_cell(self.balance_sheet, ["Total Assets", "Assets"])
        self.operating_cash_flow = self._extract_financial_cell(self.cash_flow, ["Total Cash From Operating Activities", "Operating Cash Flow"])

        earnings_per_share = self.company_info.get("trailingEps")
        self.price_to_earnings_ratio = self._safe_division(self.current_price, earnings_per_share) if earnings_per_share else self.company_info.get("trailingPE")
        self.book_value = self.company_info.get("bookValue")
        self.shares_outstanding = self.company_info.get("sharesOutstanding") or self.company_info.get("impliedSharesOutstanding")
        self.earnings_growth_rate = self.company_info.get("earningsGrowth") or self.company_info.get("earningsQuarterlyGrowth")
        self.calculated_fair_price = self._calculate_peter_lynch_fair_price(self.company_info, self.income_statement)


    def calculate(self) -> dict:
        """Constructs and returns the complete dictionary of calculated database columns for the stock symbol."""
        row = {
            SCHEMA["SYMBOL"].name: self._calc_symbol(),
            SCHEMA["SECTOR"].name: self._calc_sector(),
            SCHEMA["PRICE"].name: self._calc_price(),
            SCHEMA["FAIR_VALUE"].name: self._calc_fair_value(),
            SCHEMA["YIELD_1Y"].name: self._calc_yield_1y(),
            SCHEMA["YIELD_5Y"].name: self._calc_yield_5y(),
            SCHEMA["TTR_1Y"].name: self._calc_ttr_1y(),
            SCHEMA["TTR_3Y"].name: self._calc_ttr_3y(),
            SCHEMA["DGR_1Y"].name: self._calc_dgr_1y(),
            SCHEMA["DGR_3Y"].name: self._calc_dgr_3y(),
            SCHEMA["DGR_5Y"].name: self._calc_dgr_5y(),
            SCHEMA["DGR_10Y"].name: self._calc_dgr_10y(),
            SCHEMA["CHOWDER"].name: self._calc_chowder(),
            SCHEMA["ROE"].name: self._calc_roe(),
            SCHEMA["NPM"].name: self._calc_npm(),
            SCHEMA["ROTC"].name: self._calc_rotc(),
            SCHEMA["CUR_R"].name: self._calc_cur_r(),
            SCHEMA["EPS_1Y"].name: self._calc_eps_1y(),
            SCHEMA["CF_SHARE"].name: self._calc_cf_share(),
            SCHEMA["PAYOUT_RATIO"].name: self._calc_payout_ratio(),
            SCHEMA["DEBT_CAPITAL"].name: self._calc_debt_capital(),
            SCHEMA["NET_WORTH"].name: self._calc_net_worth(),
            SCHEMA["REVENUE_1Y"].name: self._calc_revenue_1y(),
            SCHEMA["PEG"].name: self._calc_peg(),
            SCHEMA["P_E"].name: self._calc_p_e(),
            SCHEMA["P_BV"].name: self._calc_p_bv(),
            SCHEMA["FAIR_PRICE"].name: self._calc_fair_price(),
            SCHEMA["PRICE_LOW"].name: self._calc_price_low(),
            SCHEMA["PRICE_HIGH"].name: self._calc_price_high(),
            SCHEMA["CUR_DIV"].name: self._calc_cur_div(),
            SCHEMA["PREV_DIV"].name: self._calc_prev_div(),
            SCHEMA["NUM_DIV_1Y"].name: self._calc_num_div_1y(),
            SCHEMA["DIV_1Y"].name: self._calc_div_1y(),
            SCHEMA["PAY_DATE"].name: self._calc_pay_date(),
            SCHEMA["EX_DATE"].name: self._calc_ex_date(),
            SCHEMA["COMPANY"].name: self._calc_company(),
            SCHEMA["INDUSTRY"].name: self._calc_industry(),
            SCHEMA["UPDATED_AT"].name: self._calc_updated_at(),
        }
        return self._process_row(row)


    def _process_row(self, row: dict) -> dict:
        new_row = row.copy()
        for k, v in row.items():
            if k not in SCHEMA: continue
            col_def = SCHEMA[k]
            if col_def.data_type == "REAL":
                if v is None:
                    new_row[k] = None
                else:
                    val = float(v)
                    if col_def.unit == "%":
                        val = val * 100
                    new_row[k] = round(val, 4)
            else:
                new_row[k] = v
        return new_row


    # Per-column calculation methods

    def _calc_symbol(self) -> str:
        return self.symbol

    def _calc_sector(self) -> str | None:
        return self.company_info.get("sector")

    def _calc_price(self) -> float | None:
        return self.current_price

    def _calc_fair_value(self) -> float | None:
        return self._safe_division(self.current_price, self.calculated_fair_price)

    def _calc_yield_1y(self) -> float | None:
        raw_yield = self.company_info.get("dividendYield")
        if raw_yield is not None:
            raw_yield_float = float(raw_yield)
            yield_ratio = float(self.current_dividend) / float(self.current_price) if self.current_dividend and self.current_price else None
            normalized_yield = raw_yield_float / 100 if yield_ratio and abs(raw_yield_float / 100 - yield_ratio) <= abs(raw_yield_float - yield_ratio) else raw_yield_float
            if normalized_yield > 1:
                normalized_yield = normalized_yield / 100
            return normalized_yield
        return None

    def _calc_yield_5y(self) -> float | None:
        return self._normalize_five_year_dividend_yield(
            self.company_info.get("fiveYearAvgDividendYield"),
            self.current_dividend,
            self.current_price
        )

    def _calc_ttr_1y(self) -> float | None:
        return self.ttr_1y

    def _calc_ttr_3y(self) -> float | None:
        return self.ttr_3y

    def _calc_dgr_1y(self) -> float | None:
        return self.dividend_growth_rates.get(1)

    def _calc_dgr_3y(self) -> float | None:
        return self.dividend_growth_rates.get(3)

    def _calc_dgr_5y(self) -> float | None:
        return self.dividend_growth_rates.get(5)

    def _calc_dgr_10y(self) -> float | None:
        return self.dividend_growth_rates.get(10)

    def _calc_chowder(self) -> float | None:
        dgr_5y = self.dividend_growth_rates.get(5)
        yield_1y = self._calc_yield_1y()
        return float(yield_1y) + float(dgr_5y) if yield_1y is not None and dgr_5y is not None else None

    def _calc_roe(self) -> float | None:
        return self.company_info.get("returnOnEquity")

    def _calc_npm(self) -> float | None:
        return self.company_info.get("profitMargins") or self._safe_division(self.net_income, self.total_revenue)

    def _calc_rotc(self) -> float | None:
        capital = (float(self.total_assets or 0) - float(self.current_liabilities or 0)) if self.total_assets and self.current_liabilities else None
        rotc_first = self._safe_division(self.operating_income, capital)
        rotc_second = self._safe_division(self.ebit_earnings, float(self.total_debt or 0) + float(self.total_equity or 0))
        return rotc_first or rotc_second

    def _calc_cur_r(self) -> float | None:
        return self._safe_division(self.current_assets, self.current_liabilities)

    def _calc_eps_1y(self) -> float | None:
        return self.earnings_growth_rate

    def _calc_cf_share(self) -> float | None:
        return self._safe_division(self.operating_cash_flow, self.shares_outstanding)

    def _calc_payout_ratio(self) -> float | None:
        return self.company_info.get("payoutRatio")

    def _calc_debt_capital(self) -> float | None:
        if self.total_debt is not None and self.total_equity is not None and (float(self.total_debt) + float(self.total_equity)) > 0:
            return (float(self.total_debt) / (float(self.total_debt) + float(self.total_equity))) * 100
        debt_to_equity = self.company_info.get("debtToEquity")
        if debt_to_equity is not None:
            return (float(debt_to_equity) / (100.0 + float(debt_to_equity))) * 100
        return None

    def _calc_revenue_1y(self) -> float | None:
        return self.company_info.get("revenueGrowth")

    def _calc_peg(self) -> float | None:
        peg_ratio = self.company_info.get("pegRatio")
        if peg_ratio is not None:
            return peg_ratio
        if self.price_to_earnings_ratio and self.earnings_growth_rate and self.earnings_growth_rate > 0:
            return self._safe_division(self.price_to_earnings_ratio, float(self.earnings_growth_rate) * 100)
        return None

    def _calc_p_e(self) -> float | None:
        return self.price_to_earnings_ratio

    def _calc_p_bv(self) -> float | None:
        if self.book_value:
            return self._safe_division(self.current_price, self.book_value)
        return self.company_info.get("priceToBook")

    def _calc_fair_price(self) -> float | None:
        return self.calculated_fair_price

    def _calc_price_low(self) -> float | None:
        return self.company_info.get("fiftyTwoWeekLow")

    def _calc_price_high(self) -> float | None:
        return self.company_info.get("fiftyTwoWeekHigh")

    def _calc_cur_div(self) -> float | None:
        return self.current_dividend

    def _calc_prev_div(self) -> float | None:
        return self.previous_dividend

    def _calc_num_div_1y(self) -> int:
        return self.dividend_count_last_year

    def _calc_div_1y(self) -> float | None:
        if self.dividends_last_twelve_months is not None and not self.dividends_last_twelve_months.empty:
            return float(self.dividends_last_twelve_months.sum())
        trailing_rate = self.company_info.get("trailingAnnualDividendRate")
        if trailing_rate is not None:
            return float(trailing_rate)
        if self.current_dividend is not None and self.dividend_count_last_year > 0:
            return float(self.current_dividend * self.dividend_count_last_year)
        return None

    def _calc_pay_date(self) -> str | None:
        return self.payment_date

    def _calc_ex_date(self) -> str | None:
        return self.ex_dividend_date

    def _calc_company(self) -> str | None:
        return self.company_info.get("shortName") or self.company_info.get("longName")

    def _calc_industry(self) -> str | None:
        return self.company_info.get("industry")

    def _calc_net_worth(self) -> float | None:
        if self.total_equity is not None:
            return float(self.total_equity)
        if self.book_value is not None and self.shares_outstanding is not None:
            try:
                return float(self.book_value) * float(self.shares_outstanding)
            except (TypeError, ValueError):
                pass
        return None

    def _calc_updated_at(self) -> str | None:
        return format_date(datetime.now(timezone.utc))


    # Helper methods

    def _safe_division(self, numerator: float | None, denominator: float | None) -> float | None:
        """Safely divides numerator by denominator, returning None on zero division or invalid types."""
        try:
            if numerator is None or denominator is None or float(denominator) == 0:
                return None
            return float(numerator) / float(denominator)
        except (TypeError, ValueError):
            return None


    def _extract_financial_cell(self, financial_dataframe: pd.DataFrame | None, metric_names: list[str]) -> float | None:
        """Extracts a specific metric value from a financial statement DataFrame matching any of the given names."""
        try:
            if financial_dataframe is None or len(financial_dataframe) == 0:
                return None
            labels = {str(index).lower(): index for index in financial_dataframe.index}
            for metric_name in metric_names:
                key = labels.get(metric_name.lower())
                if key is not None:
                    value = financial_dataframe.loc[key].iloc[0]
                    return None if value != value else float(value)
            for label, index in labels.items():
                for metric_name in metric_names:
                    if metric_name.lower() in label:
                        value = financial_dataframe.loc[index].iloc[0]
                        return None if value != value else float(value)
            return None
        except Exception:
            return None


    def _calculate_compound_annual_growth_rate(self, start_value: float, end_value: float, number_of_years: int) -> float | None:
        """Calculates Compound Annual Growth Rate (CAGR) between start and end values over a given number of years."""
        try:
            if not start_value or not end_value or start_value <= 0 or end_value <= 0 or number_of_years <= 0:
                return None
            return (end_value / start_value) ** (1 / number_of_years) - 1
        except (TypeError, ZeroDivisionError):
            return None


    def _calculate_dividend_growth_rate(self, dividend_series: pd.Series | None, years: int) -> float | None:
        """Calculates historical dividend growth rate over specified number of years using annual sums."""
        try:
            if dividend_series is None or len(dividend_series) == 0:
                return None
            series = pd.Series(dividend_series)
            series.index = pd.to_datetime(series.index)
            yearly_dividends = series.groupby(series.index.year).sum().sort_index()
            if len(yearly_dividends) and int(yearly_dividends.index[-1]) == datetime.now().year:
                yearly_dividends = yearly_dividends.iloc[:-1]
            if len(yearly_dividends) < years + 1:
                return None
            cagr = self._calculate_compound_annual_growth_rate(
                float(yearly_dividends.iloc[-years - 1]),
                float(yearly_dividends.iloc[-1]),
                years
            )
            return min(0.50, cagr) if cagr is not None else None
        except Exception:
            return None


    def _calculate_peter_lynch_fair_price(self, company_info: dict, income_statement: pd.DataFrame | None) -> float | None:
        """Calculates fair price using Peter Lynch method based on EPS and 5-year net income CAGR."""
        earnings_per_share = company_info.get("trailingEps")
        if earnings_per_share is None or income_statement is None or len(income_statement) == 0:
            return None
        try:
            labels = {label.lower(): index for index, label in enumerate(income_statement.index)}
            net_income_key = None
            for candidate_name in ("net income", "net income common stockholders"):
                if candidate_name in labels:
                    net_income_key = labels[candidate_name]
                    break
            if net_income_key is None:
                return None
            row = income_statement.iloc[net_income_key].dropna().sort_index()
            if len(row) < 2:
                return None
            num_years = min(5, len(row) - 1)
            initial_val = float(row.iloc[-num_years - 1])
            final_val = float(row.iloc[-1])
            if initial_val <= 0 or final_val <= 0:
                return None
            cagr = (final_val / initial_val) ** (1 / num_years) - 1
            growth_rate = max(5.0, min(25.0, cagr * 100))
            return float(earnings_per_share) * growth_rate
        except Exception:
            return None


    def _normalize_five_year_dividend_yield(self, raw_yield: float | None, current_dividend: float | None, current_price: float | None) -> float | None:
        """Normalizes 5-year average dividend yield to handle percentage scale discrepancies."""
        try:
            if raw_yield is None:
                return None
            raw_yield_float = float(raw_yield)
            calculated_ratio = float(current_dividend) / float(current_price) if current_dividend and current_price else None
            return (
                raw_yield_float / 100
                if calculated_ratio and abs(raw_yield_float / 100 - calculated_ratio) <= abs(raw_yield_float - calculated_ratio)
                else raw_yield_float
            )
        except Exception:
            return None


    def _calculate_ttr(self) -> tuple[float | None, float | None]:
        """Calculates 1-year and 3-year total return (ttr_1y, ttr_3y) from history and dividends."""
        try:
            hist = self.history
            if hist is None or len(hist) == 0:
                return None, None
            close = hist["Close"].dropna()
            if len(close) < 2:
                return None, None
            now = close.iloc[-1]
            idx = close.index.tz_convert(None) if close.index.tz is not None else close.index

            def price_asof(days: int):
                cutoff = idx[-1] - pd.Timedelta(days=days)
                past = close[idx <= cutoff]
                return float(past.iloc[-1]) if len(past) else float(close.iloc[0])

            def div_asof(days: int):
                try:
                    if self.dividend_series is None or len(self.dividend_series) == 0:
                        return 0.0
                    s = pd.Series(self.dividend_series)
                    s.index = pd.to_datetime(s.index).tz_convert(None) if s.index.tz is not None else pd.to_datetime(s.index)
                    return float(s[s.index >= (idx[-1] - pd.Timedelta(days=days))].sum())
                except Exception:
                    return 0.0

            p1, p3 = price_asof(365), price_asof(365 * 3)

            def calc_total_return(start_price, end_price, dividends, years: int = 1):
                try:
                    cum = (float(end_price) - float(start_price) + float(dividends or 0)) / start_price
                    if years <= 1:
                        return cum
                    return (1.0 + cum) ** (1.0 / years) - 1.0
                except: return None

            return (
                calc_total_return(p1, now, div_asof(365), 1),
                calc_total_return(p3, now, div_asof(365 * 3), 3),
            )
        except Exception:
            return None, None
