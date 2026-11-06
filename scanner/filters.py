import pandas as pd

def apply_optional_filters(row: dict, cfg: dict) -> bool:
    if cfg.get("use_rsi") and not (cfg["rsi_min"] <= row.get("RSI", float("nan")) <= cfg["rsi_max"]):
        return False
    if cfg.get("use_volume") and not (row.get("Volume Ratio", 0) >= cfg["volume_multiplier"]):
        return False
    if cfg.get("use_trend"):
        if not row.get("Above EMA200", False):
            return False
        if cfg.get("ema200_rising") and not row.get("EMA200 Rising", False):
            return False
    if row.get("Current Price", 0) < cfg.get("min_price", 0):
        return False
    if cfg.get("use_liquidity"):
        if row.get("Average Volume 20D", 0) < cfg["min_avg_volume"]:
            return False
        if row.get("Average Traded Value 20D", 0) < cfg["min_avg_value"]:
            return False
    if cfg.get("use_price_strength"):
        if row.get("1M Return %", -1e9) < cfg["min_1m_return"]:
            return False
        if row.get("3M Return %", -1e9) < cfg["min_3m_return"]:
            return False
    return True
