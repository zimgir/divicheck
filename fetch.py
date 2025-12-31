

def add_beta_column(rows):

    BENCHMARK = "^GSPC"
    LOOKBACK_YEARS = 2

    end = pd.Timestamp.today()
    start = end - pd.DateOffset(years=LOOKBACK_YEARS)

    print("Downloading benchmark data...")
    market = yf.download(BENCHMARK, start=start, end=end, progress=False)
    market_returns = market["Adj Close"].pct_change().dropna()

    betas = []

    for symbol in rows["Symbol"]:
        try:
            stock = yf.download(symbol, start=start, end=end, progress=False)
            stock_returns = stock["Adj Close"].pct_change().dropna()

            aligned = pd.concat(
                [stock_returns, market_returns],
                axis=1,
                join="inner"
            )

            if len(aligned) < 60:
                betas.append(np.nan)
                continue

            beta = compute_beta(aligned.iloc[:, 0], aligned.iloc[:, 1])
            betas.append(round(beta, 3))

        except Exception:
            betas.append(np.nan)

    df["Beta"] = betas


def update_eps_column(rows):
    pass