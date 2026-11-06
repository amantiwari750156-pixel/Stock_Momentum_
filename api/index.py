from __future__ import annotations
import os, sys, tempfile, json
from pathlib import Path
from typing import Any
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scanner.data_fetcher import fetch_universe, fetch_history
from scanner.indicators import add_indicators
from scanner.crossover import crossover_events, dema_crossover_events, price_crossover_events
from scanner.scanner_engine import scan_symbols

DATA_DIR = Path(tempfile.gettempdir()) / "india_momentum_scanner"
os.environ["MOMENTUM_CACHE_DIR"] = str(DATA_DIR / "price_cache")
DATA_DIR.mkdir(parents=True, exist_ok=True)
UNIVERSE_FILE = DATA_DIR / "stock_universe.csv"
CACHE_DIR = DATA_DIR / "price_cache"

app = FastAPI(title="India Momentum Scanner API", version="1.0.0")


@app.get("/", include_in_schema=False)
def dashboard():
    """Display the India Momentum Scanner dashboard."""
    dashboard_file = ROOT / "index.html"

    if not dashboard_file.exists():
        raise HTTPException(
            status_code=500,
            detail="Dashboard file index.html is missing from the deployment."
        )

    return FileResponse(
        dashboard_file,
        media_type="text/html"
    )


class ScanRequest(BaseModel):
    universe: str = "Nifty 50 (static list)"
    offset: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)
    consolidation_period: str = "100 trading days"
    max_consolidation: float = Field(20, ge=5, le=50)
    crossovers: list[str] = ["50/100", "50/200", "100/200"]
    dema_crossovers: list[str] = []
    price_crossovers: list[str] = []
    price_cross_direction: str = "BOTH"
    crossover_mode: str = "ANY"
    lookback: int = Field(5, ge=1, le=20)
    use_rsi: bool = True
    rsi_min: float = 50
    rsi_max: float = 70
    use_volume: bool = False
    volume_multiplier: float = 1.5
    use_trend: bool = False
    ema200_rising: bool = False
    use_liquidity: bool = False
    min_avg_volume: float = 100000
    min_avg_value: float = 10000000
    min_price: float = 10
    use_price_strength: bool = False
    min_1m_return: float = 0
    min_3m_return: float = 0
    refresh: bool = False

NIFTY50 = ["ADANIENT","ADANIPORTS","APOLLOHOSP","ASIANPAINT","AXISBANK","BAJAJ-AUTO","BAJFINANCE","BAJAJFINSV","BEL","BHARTIARTL","CIPLA","COALINDIA","DRREDDY","EICHERMOT","ETERNAL","GRASIM","HCLTECH","HDFCBANK","HDFCLIFE","HEROMOTOCO","HINDALCO","HINDUNILVR","ICICIBANK","INDUSINDBK","INFY","ITC","JIOFIN","JSWSTEEL","KOTAKBANK","LT","M&M","MARUTI","NESTLEIND","NTPC","ONGC","POWERGRID","RELIANCE","SBILIFE","SBIN","SHRIRAMFIN","SUNPHARMA","TATACONSUM","TATASTEEL","TCS","TECHM","TITAN","TRENT","ULTRACEMCO","WIPRO"]

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "India Momentum Scanner", "version": "1.0.0"}

@app.get("/api/universe")
def universe():
    df = fetch_universe(UNIVERSE_FILE)
    return {"count": int(len(df)), "symbols": df[["SYMBOL", "NAME OF COMPANY"]].fillna("").to_dict("records"), "warning": df.attrs.get("universe_warning")}

@app.post("/api/scan")
def scan(req: ScanRequest):
    try:
        df = fetch_universe(UNIVERSE_FILE, refresh=req.refresh)
        if req.universe == "Nifty 50 (static list)":
            df = df[df["SYMBOL"].isin(NIFTY50)]
            # Preserve the complete static index list if NSE's live file is unavailable.
            if df.empty:
                df = pd.DataFrame({"SYMBOL": NIFTY50, "NAME OF COMPANY": NIFTY50})
        elif req.universe == "First 500 NSE EQ (subset)":
            df = df.head(500)
        elif req.universe == "Fallback sample":
            sample = ["RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","ITC","SBIN","BHARTIARTL","LT","AXISBANK","KOTAKBANK","SUNPHARMA","MARUTI","TATAMOTORS","NTPC"]
            df = df[df["SYMBOL"].isin(sample)]
        total = len(df)
        batch = df.iloc[req.offset:req.offset + req.limit].copy()
        cfg = req.model_dump(exclude={"universe", "offset", "limit", "refresh"})
        results, failures = scan_symbols(batch, cfg, refresh=req.refresh)
        safe_results = json.loads(results.replace([float("inf"), float("-inf")], float("nan")).to_json(orient="records"))
        safe_failures = json.loads(failures.to_json(orient="records"))
        return {"offset": req.offset, "processed": len(batch), "total": total,
                "done": req.offset + len(batch) >= total,
                "results": safe_results, "failures": safe_failures,
                "universe_warning": df.attrs.get("universe_warning")}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.get("/api/chart/{symbol}")
def chart(symbol: str):
    try:
        raw = fetch_history(symbol.upper(), period="3y", cache_dir=CACHE_DIR)
        full = add_indicators(raw).dropna(subset=["DEMA50", "EMA50", "EMA100", "EMA200"])
        df = full.tail(756)
        events = {}
        events.update(crossover_events(full, 20))
        events.update(dema_crossover_events(full, 20))
        events.update(price_crossover_events(full, 20, "BOTH"))
        records = []
        for idx, row in df.iterrows():
            records.append({"date": idx.strftime("%Y-%m-%d"), "open": float(row.Open), "high": float(row.High), "low": float(row.Low), "close": float(row.Close), "volume": float(row.Volume), "dema50": float(row.DEMA50), "ema50": float(row.EMA50), "ema100": float(row.EMA100), "ema200": float(row.EMA200), "rsi": None if pd.isna(row.RSI) else float(row.RSI)})
        return {"symbol": symbol.upper(), "data": records, "crossovers": {k: str(v.date()) if v is not None else None for k, v in events.items()}, "source": "Yahoo Finance (unofficial)", "latest_date": df.index[-1].strftime("%Y-%m-%d")}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not load {symbol}: {exc}")

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    return JSONResponse(status_code=500, content={"detail": "Unexpected server error. Check deployment logs."})
