import numpy as np
import pandas as pd


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add EMA, 50-session DEMA, Wilder RSI, volume and return indicators."""
    out = df.copy()
    close = out["Close"].astype(float)
    for period in (50, 100, 200):
        out[f"EMA{period}"] = close.ewm(span=period, adjust=False, min_periods=period).mean()
    # DEMA(n) = 2 * EMA(price, n) - EMA(EMA(price, n), n)
    ema50_first = close.ewm(span=50, adjust=False, min_periods=50).mean()
    ema50_second = ema50_first.ewm(span=50, adjust=False, min_periods=50).mean()
    out["DEMA50"] = 2 * ema50_first - ema50_second

    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    avg_loss = loss.ewm(alpha=1/14, adjust=False, min_periods=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    out["RSI"] = 100 - (100 / (1 + rs))
    out.loc[(avg_loss == 0) & (avg_gain > 0), "RSI"] = 100
    out.loc[(avg_gain == 0) & (avg_loss > 0), "RSI"] = 0
    out["VolumeAvg20"] = out["Volume"].rolling(20, min_periods=20).mean()
    out["VolumeRatio"] = out["Volume"] / out["VolumeAvg20"]
    out["AvgVolume20"] = out["Volume"].rolling(20, min_periods=20).mean()
    out["AvgTradedValue20"] = (out["Close"] * out["Volume"]).rolling(20, min_periods=20).mean()
    for label, periods in (("1M", 21), ("3M", 63), ("6M", 126)):
        out[f"Return{label}"] = close.pct_change(periods) * 100
    out["EMA200Rising"] = out["EMA200"] > out["EMA200"].shift(20)
    return out


def relative_strength(stock_df: pd.DataFrame, benchmark_df: pd.DataFrame) -> float:
    """3-month stock return less benchmark return, in percentage points."""
    if stock_df is None or benchmark_df is None or len(stock_df) < 64 or len(benchmark_df) < 64:
        return float("nan")
    stock_ret = stock_df["Close"].iloc[-1] / stock_df["Close"].iloc[-64] - 1
    bench_ret = benchmark_df["Close"].iloc[-1] / benchmark_df["Close"].iloc[-64] - 1
    return float((stock_ret - bench_ret) * 100)
