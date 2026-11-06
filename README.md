# India Momentum & EMA Crossover Scanner

A local Streamlit research scanner for NSE-listed equities. It screens fresh bullish EMA crossovers, price consolidation, RSI, volume, trend, liquidity and price strength. It is not a trading system.

## Mac installation

1. Install Python 3.10 or later from https://www.python.org/downloads/macos/ if it is not already installed.
2. Extract `India_Momentum_Scanner.zip` to a folder you can find (for example, Documents).
3. Open the extracted folder in Finder.
4. Right-click `run_mac.command` → Open. Confirm Open if macOS displays a security prompt.
5. A Terminal window will create a private `.venv`, install packages and launch Streamlit.
6. Open the local address printed in Terminal (usually http://localhost:8501). Keep Terminal open while using the scanner.
7. To stop the app, click Terminal and press Control+C.

If macOS blocks the launcher, open Terminal, type `chmod +x ` (include a trailing space), drag `run_mac.command` into Terminal, press Enter, then double-click the launcher again.

## Windows

Install Python 3.10+, extract the ZIP, and double-click `run_windows.bat`.

## First use

- Start with a small universe or use the maximum-stocks setting to test the workflow.
- Select one or more EMA crossovers and choose ANY or ALL.
- Choose the consolidation window and maximum range.
- Run the scan. The app saves results to `data/scans.db`.
- Use the chart tab to load an individual NSE symbol (without `.NS`).
- Export qualifying results or failed-download details to CSV.

## Data and limitations

- Yahoo Finance through yfinance is unofficial and is not an exchange-authorised real-time feed. Coverage, freshness, corporate-action treatment and rate limits can vary.
- The NSE public equity CSV is attempted first and cached. If unavailable, the app uses a small fallback universe. The displayed universe size should be checked before scanning.
- The NSE EQ list is not a guaranteed complete SME list. SME inclusion is not implemented because reliable free coverage is not assured.
- The first-500 selector takes the first 500 securities in the available NSE EQ file; it is a convenience scan subset, **not verified Nifty 500 membership**.
- Full-universe downloads can be slow and may be throttled. Failed symbols appear in the data-quality report.
- Historical prices are auto-adjusted by yfinance. The latest available close is not necessarily live.
- Three years of history are requested to support 200 EMA, 252-session consolidation and return calculations.
- The scanner reports signals for further research; it does not issue buy/sell recommendations or execute trades.

## Calculations

- EMA: exponential moving average, `adjust=False`.
- RSI: 14-session Wilder-style smoothing.
- Fresh crossover: previous session fast EMA <= slow EMA and current session fast EMA > slow EMA.
- Lookback: last 1, 3, 5, 10 or 20 trading sessions.
- Consolidation: `(highest high - lowest low) / average close * 100`.
- Volume ratio: latest volume / 20-session average volume.
- Relative strength: stock 3-month return minus Nifty 50 3-month return.

## Tests

Run from the project folder:

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```

The test suite uses deterministic synthetic data and does not require Yahoo Finance.
