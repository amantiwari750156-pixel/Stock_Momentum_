import math
import pandas as pd
from .data_fetcher import fetch_history
from .indicators import add_indicators, relative_strength
from .crossover import crossover_events, dema_crossover_events, price_crossover_events, selected_crossover_match
from .consolidation import consolidation_metrics
from .filters import apply_optional_filters

def scan_symbols(universe: pd.DataFrame, cfg: dict, progress=None, refresh: bool = False, cache_dir="data/price_cache"):
    benchmark = None
    try:
        benchmark = add_indicators(fetch_history("^NSEI", period="3y", cache_dir=cache_dir, refresh=refresh))
    except Exception:
        pass
    results, failures = [], []
    symbols = universe[["SYMBOL", "NAME OF COMPANY"]].drop_duplicates("SYMBOL").to_dict("records")
    total = len(symbols)
    for i, item in enumerate(symbols, 1):
        symbol, company = str(item["SYMBOL"]).strip(), str(item["NAME OF COMPANY"]).strip()
        try:
            raw = fetch_history(symbol, period="3y", retries=3, pause=1.2, cache_dir=cache_dir, refresh=refresh)
            if len(raw) < 253:
                raise ValueError(f"Insufficient history ({len(raw)} sessions; 253 preferred)")
            df = add_indicators(raw)
            latest = df.iloc[-1]
            if pd.isna(latest["EMA200"]) or pd.isna(latest["RSI"]):
                raise ValueError("Insufficient data for indicators")
            events = {}
            events.update(crossover_events(df, cfg["lookback"]))
            events.update(dema_crossover_events(df, cfg["lookback"]))
            events.update(price_crossover_events(df, cfg["lookback"], cfg.get("price_cross_direction", "BOTH")))
            selected_events = (cfg.get("crossovers", []) + cfg.get("dema_crossovers", []) + cfg.get("price_crossovers", []))
            qualifies, matched = selected_crossover_match(events, selected_events, cfg["crossover_mode"])
            if not qualifies:
                continue
            try:
                cons = consolidation_metrics(df, cfg["consolidation_period"])
            except ValueError:
                continue
            row = {
                "Stock Symbol": symbol, "Company Name": company,
                "Current Price": float(latest["Close"]), "EMA 50": float(latest["EMA50"]),
                "EMA 100": float(latest["EMA100"]), "EMA 200": float(latest["EMA200"]),
                "DEMA 50": float(latest["DEMA50"]),
                "Price vs DEMA50": "Above" if latest["Close"] > latest["DEMA50"] else "Below",
                "Price vs EMA50": "Above" if latest["Close"] > latest["EMA50"] else "Below",
                "Price vs EMA100": "Above" if latest["Close"] > latest["EMA100"] else "Below",
                "Price vs EMA200": "Above" if latest["Close"] > latest["EMA200"] else "Below",
                "Crossover Signal": ", ".join(matched) if matched else "No crossover filter",
                "Crossover Date": max((events[x] for x in matched), default=None),
                "RSI": float(latest["RSI"]),
                "Volume Ratio": float(latest["VolumeRatio"]) if pd.notna(latest["VolumeRatio"]) else 0,
                "Consolidation Period": cfg["consolidation_period"],
                "1M Return %": float(latest["Return1M"]) if pd.notna(latest["Return1M"]) else float("nan"),
                "3M Return %": float(latest["Return3M"]) if pd.notna(latest["Return3M"]) else float("nan"),
                "6M Return %": float(latest["Return6M"]) if pd.notna(latest["Return6M"]) else float("nan"),
                "Relative Strength %": relative_strength(df, benchmark) if benchmark is not None else float("nan"),
                "Above EMA200": bool(latest["Close"] > latest["EMA200"]),
                "EMA200 Rising": bool(latest["EMA200Rising"]),
                "Average Volume 20D": float(latest["AvgVolume20"]) if pd.notna(latest["AvgVolume20"]) else 0,
                "Average Traded Value 20D": float(latest["AvgTradedValue20"]) if pd.notna(latest["AvgTradedValue20"]) else 0,
                "Latest Volume": float(latest["Volume"]),
                "Data Date": str(df.index[-1].date()),
                "Data Source": "Yahoo Finance (unofficial)"
            }
            row.update(cons)
            if cfg["consolidation_period"] != "No consolidation filter" and row["Consolidation Range %"] > cfg["max_consolidation"]:
                continue
            if not apply_optional_filters(row, cfg):
                continue
            results.append(row)
        except Exception as exc:
            failures.append({"Stock Symbol": symbol, "Company Name": company, "Reason": str(exc)})
        if progress:
            progress(i / max(total,  1), f"Scanning {symbol} ({i}/{total})")
    return pd.DataFrame(results), pd.DataFrame(failures)
