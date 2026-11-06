from __future__ import annotations
import io, time
from pathlib import Path
import pandas as pd
import yfinance as yf
import requests

NSE_EQUITY_URL = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
FALLBACK = ["RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","ITC","SBIN","BHARTIARTL",
            "LT","AXISBANK","KOTAKBANK","HINDUNILVR","MARUTI","SUNPHARMA","TATAMOTORS",
            "TATASTEEL","BAJFINANCE","ASIANPAINT","HCLTECH","NTPC","POWERGRID","ONGC"]

def fetch_universe(cache_file: str | Path, refresh: bool = False) -> pd.DataFrame:
    path = Path(cache_file)
    if path.exists() and not refresh:
        try:
            cached = pd.read_csv(path)
            if {"SYMBOL", "NAME OF COMPANY"}.issubset(cached.columns):
                return cached.drop_duplicates("SYMBOL")
        except Exception:
            pass
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "text/csv,*/*"}
    try:
        response = requests.get(NSE_EQUITY_URL, headers=headers, timeout=20)
        response.raise_for_status()
        df = pd.read_csv(io.BytesIO(response.content))
        df.columns = [str(c).strip().upper() for c in df.columns]
        if "SYMBOL" not in df.columns:
            raise ValueError("NSE equity file has no SYMBOL column")
        if "NAME OF COMPANY" not in df.columns:
            df["NAME OF COMPANY"] = df["SYMBOL"]
        if "SERIES" in df.columns:
            df = df[df["SERIES"].astype(str).str.strip().eq("EQ")]
        df = df.drop_duplicates("SYMBOL")
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)
        return df
    except Exception as exc:
        if path.exists():
            try:
                return pd.read_csv(path).drop_duplicates("SYMBOL")
            except Exception:
                pass
        return pd.DataFrame({"SYMBOL": FALLBACK, "NAME OF COMPANY": FALLBACK}).assign(_source_note=f"NSE list unavailable: {exc}")

def fetch_history(symbol: str, period: str = "3y", retries: int = 3, pause: float = 1.0,
                  cache_dir: str | Path | None = None, refresh: bool = False) -> pd.DataFrame:
    ticker = symbol if symbol.startswith("^") else f"{symbol}.NS"
    cache_path = None
    if cache_dir is not None:
        cache_root = Path(cache_dir)
        cache_root.mkdir(parents=True, exist_ok=True)
        safe_name = ticker.replace("^", "INDEX_").replace(".", "_")
        cache_path = cache_root / f"{safe_name}_{period}.csv"
        if cache_path.exists() and not refresh:
            try:
                cached = pd.read_csv(cache_path, index_col=0, parse_dates=True)
                cached.index = pd.to_datetime(cached.index).tz_localize(None)
                if {"Open", "High", "Low", "Close", "Volume"}.issubset(cached.columns) and len(cached):
                    return cached[["Open", "High", "Low", "Close", "Volume"]]
            except Exception:
                pass
    last_error = None
    for attempt in range(retries):
        try:
            data = yf.download(ticker, period=period, interval="1d", auto_adjust=True,
                               progress=False, threads=False, timeout=25)
            if data is None or data.empty:
                raise ValueError("No historical data returned")
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            data = data.rename(columns={c: str(c).title() for c in data.columns})
            required = ["Open", "High", "Low", "Close", "Volume"]
            if not set(required).issubset(data.columns):
                raise ValueError("OHLCV columns missing")
            data = data[required].dropna(subset=["Close"])
            data.index = pd.to_datetime(data.index).tz_localize(None)
            data = data[~data.index.duplicated(keep="last")].sort_index()
            if cache_path is not None:
                data.to_csv(cache_path)
            return data
        except Exception as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(pause * (attempt + 1))
    raise RuntimeError(f"{ticker}: {last_error}")
