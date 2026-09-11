# DiviCheck Database Implementation Plan

## 1. Scope

Build SQLite database pipeline for DiviCheck GUI:
- Fetch stock fundamentals + dividends from yfinance
- Compute derived metrics (DGR, CHOWDER, TTR, PEG, etc.)
- Store into SQLite, filter dividend payers only
- Rebuild or update whole DB in single invocation
- Tests: statistics + query verification

## 2. Project Structure

```
divicheck/
├── tests/
│   ├── test_db.py      # Statistics print + verification queries
│ 
└── db/
    ├── db_cli.py       # CLI entry point: rebuild / update / stats
    ├── __init__.py
    ├── schema.py       # Column constants, CREATE TABLE statements
    ├── connection.py   # SQLite connection, transaction helpers
    ├── repository.py   # Insert/update/delete stock rows
    └── fetcher.py      # yfinance calls, derived metric calculations
```

## 3. Database Schema

### 3.1 Table: stocks

One row per symbol. `SYMBOL` primary key.

```sql
CREATE TABLE IF NOT EXISTS stocks (
    SYMBOL TEXT PRIMARY KEY,
    STOCK_TYPE TEXT,
    COMPANY TEXT,
    SECTOR TEXT,
    INDUSTRY TEXT,
    PRICE REAL,
    FAIR_VALUE REAL,
    YIELD_1Y REAL,
    YIELD_5Y REAL,
    DIV_1Y REAL,
    CUR_DIV REAL,
    NUM_DIV_1Y INTEGER,
    PAY_DATE TEXT,
    CHOWDER REAL,
    ROE REAL,
    PAYOUT_RATIO REAL,
    DEBT_CAPITAL REAL,
    DGR_1Y REAL,
    DGR_3Y REAL,
    DGR_5Y REAL,
    DGR_10Y REAL,
    TTR_1Y REAL,
    TTR_3Y REAL,
    EPS_1Y REAL,
    REVENUE_1Y REAL,
    NPM REAL,
    ROTC REAL,
    CUR_R REAL,
    P_E REAL,
    P_BV REAL,
    CF_SHARE REAL,
    PEG REAL,
    FAIR_PRICE REAL,
    PRICE_LOW REAL,
    PRICE_HIGH REAL,
    PREV_DIV REAL,
    EX_DATE TEXT,
    UPDATED_AT TEXT NOT NULL
);
```

### 3.2 Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_stocks_yield ON stocks(YIELD_1Y);
CREATE INDEX IF NOT EXISTS idx_stocks_sector ON stocks(SECTOR);
CREATE INDEX IF NOT EXISTS idx_stocks_industry ON stocks(INDUSTRY);
CREATE INDEX IF NOT EXISTS idx_stocks_dgr ON stocks(DGR_5Y);
CREATE INDEX IF NOT EXISTS idx_stocks_div ON stocks(CUR_DIV);
```

### 3.3 SQLite pragmas

- `PRAGMA journal_mode = WAL` — concurrent reads during writes (GUI)
- `PRAGMA synchronous = NORMAL` — balance durability/speed
- `PRAGMA foreign_keys = ON`
- `PRAGMA busy_timeout = 5000` — avoid lock errors

## 4. Data Flow

```
db/db_cli.py (CLI)
    ↓
fetcher.fetch_all(symbols)
    ↓ (batched, rate-limited)
fetcher.fetch_symbol(symbol)
    ↓
fetcher.calculate_metrics(raw_info, financials, dividends)
    ↓
repository.upsert_stock(row)
    ↓
SQLite
```

## 5. yfinance Fetching Strategy

### 5.1 Symbol universe

- Default: S&P 500 constituents (hardcoded list or fetched from Wikipedia)
- Optional: user-provided list via `--symbols file.txt`

### 5.2 Two-pass fetch (filter before expensive calls)

**Pass 1 — Cheap info scan:**
- Batch size: 50 symbols per request
- Call `Ticker(symbol).info` for each symbol
- Extract `dividendYield` and `trailingAnnualDividendRate`
- Filter: keep only symbols where `dividendYield > 0` or `trailingAnnualDividendRate > 0`
- Log skipped non-payers to `db/fetch_errors.log`

**Pass 2 — Full fetch for dividend payers only:**
- For filtered symbols, fetch `dividends` series, `history()` for TTR, `financials`, `balance_sheet`, `cashflow`
- Compute all derived metrics
- Upsert into SQLite

This avoids expensive history/financials calls for ~70% of S&P 500 that don't pay dividends.

### 5.3 Batch fetching

- Batch size: 50 symbols per request
- Sleep between batches: configurable via `--sleep` (default 1–2s)
- Retry on failure: exponential backoff (3 attempts)
- Log per-symbol failures to `db/fetch_errors.log` for manual review

### 5.4 Rate-limit avoidance

- One `Ticker` object per symbol, reuse within batch
- Cache results in memory per invocation
- Single invocation rebuilds whole DB — no repeated partial fetches
- Use `progress=False` to keep output clean

## 6. Derived Metrics (calculated, not directly fetched)

All derived values computed in `fetcher.py` from raw yfinance data:

| Metric | Formula | Source data |
|---|---|---|
| DGR_1Y / DGR_3Y / DGR_5Y / DGR_10Y | CAGR of dividend per share over N years | `Ticker.dividends` |
| DIV_1Y | Sum of dividends paid in last 12 months | `Ticker.dividends` |
| CUR_DIV | Latest trailing twelve-month dividend per share | `Ticker.dividends` |
| NUM_DIV_1Y | Count of dividend payments in last 12 months | `Ticker.dividends` |
| PAY_DATE / EX_DATE | Latest dividend date | `Ticker.dividends` |
| CHOWDER | Dividend Yield + 5Y DGR | `dividendYield` + `DGR_5Y` |
| NPM | Net income / revenue (TTM) | `income_stmt` |
| ROTC | EBIT / (debt + equity) | `income_stmt` + `balance_sheet` |
| CUR_R | Current assets / current liabilities | `balance_sheet` |
| P_E | Price / EPS (TTM) | `currentPrice` + `trailingEps` |
| P_BV | Price / book value per share | `currentPrice` + `bookValue` |
| CF_SHARE | Operating cash flow / diluted avg shares | `cashflow` + `info` |
| PEG | P/E / EPS growth (5Y) | `trailingPE` + `epsGrowth` |
| TTR_1Y / TTR_3Y | Total return = price change + dividends reinvested | `Ticker.history()` |

### 6.1 Calculation functions

```python
def cagr(start: float, end: float, years: int) -> float:
    """Compound Annual Growth Rate. Returns None if invalid."""

def calc_dividend_growth(dividends: pd.Series, years: int) -> float:
    """CAGR of dividend per share over `years`."""

def calc_chowder(dividend_yield: float, dgr_5y: float) -> float:
    """Chowder Rule: yield + 5y dividend growth."""

def calc_npm(net_income: float, revenue: float) -> float:
    """Net profit margin."""

def calc_rotc(ebit: float, total_debt: float, total_equity: float) -> float:
    """Return on total capital."""

def calc_cur_ratio(current_assets: float, current_liabilities: float) -> float:
    """Current ratio."""

def calc_peg(pe: float, eps_growth: float) -> float:
    """PEG ratio; None if growth <= 0."""

def calc_total_return(start_price: float, end_price: float, dividends: float) -> float:
    """Total return over period (price change + dividends)."""
```

### 6.2 Data mapping (yfinance → DB columns)

| DB column | yfinance field |
|---|---|
| SYMBOL | `symbol` |
| STOCK_TYPE | `asset_class` |
| COMPANY | `shortName` |
| SECTOR | `sector` |
| INDUSTRY | `industry` |
| PRICE | `currentPrice` |
| FAIR_VALUE | `targetMeanPrice` (as proxy) |
| YIELD_1Y | `dividendYield` |
| YIELD_5Y | `fiveYearAvgDividendYield` |
| DIV_1Y | sum of last 12m dividends |
| CUR_DIV | TTM dividend per share |
| NUM_DIV_1Y | count of dividends in last 12m |
| PAY_DATE | latest dividend date |
| CHOWDER | computed |
| ROE | `returnOnEquity` |
| PAYOUT_RATIO | `payoutRatio` |
| DEBT_CAPITAL | `debtToEquity` (as proxy) |
| DGR_* | computed from dividends |
| TTR_* | computed from price history |
| EPS_1Y | TTM EPS growth |
| REVENUE_1Y | TTM revenue growth |
| NPM | computed |
| ROTC | computed |
| CUR_R | computed |
| P_E | computed |
| P_BV | computed |
| CF_SHARE | computed |
| PEG | computed |
| FAIR_PRICE | `targetMeanPrice` |
| PRICE_LOW | 52-week low |
| PRICE_HIGH | 52-week high |
| PREV_DIV | previous dividend per share |
| EX_DATE | latest ex-dividend date |
| UPDATED_AT | ISO-8601 timestamp of fetch |

## 7. Update vs Rebuild

### 7.1 Rebuild (`--rebuild`)
- Drop existing `stocks` table
- Create fresh schema
- Fetch all symbols, insert rows
- Single transaction for atomicity

### 7.2 Update (`--update`)
- Keep existing rows
- Upsert fetched rows (`INSERT ... ON CONFLICT(SYMBOL) DO UPDATE`)
- Remove symbols no longer in universe (optional flag `--prune`)

## 8. Error Handling

- Per-symbol try/except; log failures, continue
- Retry with exponential backoff on transient yfinance errors
- Missing fields → `None`, never crash
- Division by zero → `None`
- Invalid dates → `None`

## 9. Tests

### 9.1 `tests/test_db.py`

Prints database statistics:
- Total rows
- Count by sector
- Average/median yield
- Top 10 by dividend yield
- Top 10 by CHOWDER

Query checks:
- All rows have non-null SYMBOL
- All rows are dividend payers (`CUR_DIV > 0`)
- No duplicate SYMBOLs
- Derived metrics are within plausible ranges (e.g., `0 <= YIELD_1Y <= 1`)
- `CHOWDER == YIELD_1Y + DGR_5Y` (within tolerance)
- P_E, P_BV > 0 for rows with data

### 9.2 Test helpers

- `connect_test_db(path)` — opens temp SQLite DB
- `populate_test_data()` — inserts known-good fixture rows
- `run_verification_queries()` — executes the check queries above

## 10. CLI

```bash
python db/db_cli.py rebuild --symbols sp500 --sleep 1
python db/db_cli.py update --symbols mylist.txt --prune
python db/db_cli.py stats
```

## 11. Dependencies

- `yfinance` — market data
- `pandas` — dataframes for batched history
- `sqlite3` (stdlib) — database
- `requests` (optional, for symbol universe fetch)

## 12. Implementation Order

1. `db/__init__.py` — package init
2. `db/schema.py` — column constants + schema SQL
3. `db/connection.py` — connection + pragmas
4. `db/repository.py` — upsert + stats queries
5. `db/fetcher.py` — yfinance batch fetch + derived metrics
6. `db/db_cli.py` — CLI entry point
7. `tests/test_db.py` — statistics + verification
8. Verify: run `python db/db_cli.py rebuild`, then `python tests/test_db.py`
