import pandas as pd

PERIODS = {"100 trading days": 100, "200 trading days": 200, "1 year (252 sessions)": 252}

def consolidation_metrics(df: pd.DataFrame, period: str) -> dict:
    if period == "No consolidation filter":
        return {"Consolidation High": float("nan"), "Consolidation Low": float("nan"),
                "Consolidation Range %": float("nan"), "Distance from High %": float("nan"),
                "Distance from Low %": float("nan")}
    n = PERIODS[period]
    window = df.tail(n)
    if len(window) < n:
        raise ValueError(f"Insufficient history: need {n} sessions, found {len(window)}")
    high = float(window["High"].max())
    low = float(window["Low"].min())
    avg_close = float(window["Close"].mean())
    price = float(df["Close"].iloc[-1])
    width = ((high - low) / avg_close) * 100 if avg_close else float("nan")
    return {"Consolidation High": high, "Consolidation Low": low,
            "Consolidation Range %": width,
            "Distance from High %": ((high - price) / high) * 100 if high else float("nan"),
            "Distance from Low %": ((price - low) / low) * 100 if low else float("nan")}
