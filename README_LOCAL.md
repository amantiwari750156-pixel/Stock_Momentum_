# India Momentum Scanner — Local Mac Web Dashboard

A professional dark-themed local Streamlit website for NSE equity research. Runs on your Mac and opens at `http://localhost:8501`. It is not an automated trading system.

## Mac installation

1. Download and extract `India_Momentum_Scanner_Local_Web.zip`.
2. Install Python 3.10 or later from https://www.python.org/downloads/macos/ if needed.
3. Open the extracted folder in Finder.
4. Right-click `run_mac.command` and select **Open**. Confirm the security prompt if macOS asks. Do not disable Gatekeeper globally.
5. The launcher creates a private `.venv`, installs dependencies, and starts the dashboard. Keep Terminal open.
6. Open `http://localhost:8501` in Chrome or Safari.
7. Stop the app with Control+C in Terminal.

If macOS says `Permission denied`, open Terminal and run (adjust the path if extracted elsewhere):

```bash
cd ~/Downloads/India_Momentum_Scanner
chmod u+x run_mac.command
bash ./run_mac.command
```

If it says `Operation not permitted`, move the extracted folder to Desktop and try again. Do not grant Full Disk Access unless macOS specifically identifies a protected-folder access issue.

## Windows

Install Python 3.10+, extract the ZIP, then double-click `run_windows.bat`.

## Included features

- NSE EQ stock list refresh and local cache; fallback list if NSE is inaccessible.
- Static Nifty 50 selector and first-500 NSE EQ convenience subset (not verified Nifty 500 membership).
- Fresh bullish EMA 50/100, 50/200 and 100/200 crossovers.
- 1, 3, 5, 10 and 20 trading-session crossover lookback; ANY/ALL selection.
- 100, 200 and 252-session consolidation or no consolidation filter.
- Configurable maximum consolidation range.
- RSI(14), volume ratio, EMA200 trend, rising EMA200, minimum price, liquidity and price-strength filters.
- Relative performance versus Nifty 50.
- Candlestick chart with EMA overlays, consolidation boundaries, crossover markers, volume and RSI.
- CSV export, SQLite scan history and data-failure report.
- Local historical-price cache and a force-refresh option.

## Data limitations

- Yahoo Finance via `yfinance` is unofficial, not an NSE-authorised live feed, and may be delayed, incomplete, throttled or unavailable.
- NSE public equity CSV access may fail. The app uses a cached universe if available, otherwise a small fallback sample. Check the universe count and warning before scanning.
- SME coverage is not guaranteed and is not presented as a complete universe.
- First-500 is a convenience subset, not verified Nifty 500 constituents.
- Full-universe scans can take a long time. Failed downloads and insufficient histories are shown separately.
- Prices use `auto_adjust=True`; the latest close is not necessarily live.
- Three years of history are requested for 200 EMA and 252-session calculations.
- Relative strength is stock 3-month return minus Nifty 50 3-month return, in percentage points.
- Consolidation alone does not confirm a breakout.

## Tests

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```

The unit tests use deterministic synthetic data. Passing them does not prove external NSE/Yahoo connectivity or a successful launch on your Mac.
