import pandas as pd

PAIRS = {
    "50/100": ("EMA50", "EMA100"),
    "50/200": ("EMA50", "EMA200"),
    "100/200": ("EMA100", "EMA200"),
}
DEMA_PAIRS = {
    "DEMA50/EMA100": ("DEMA50", "EMA100"),
    "DEMA50/EMA50": ("DEMA50", "EMA50"),
    "DEMA50/EMA200": ("DEMA50", "EMA200"),
}
PRICE_AVERAGES = {"DEMA50": "DEMA50", "EMA50": "EMA50", "EMA100": "EMA100", "EMA200": "EMA200"}


def _cross_dates(df: pd.DataFrame, left: str, right: str, lookback: int, direction: str):
    if len(df) < 2 or left not in df.columns or right not in df.columns:
        return None
    tail = df.tail(max(int(lookback), 1) + 1)
    if direction == "bullish":
        crossed = (tail[left].shift(1) <= tail[right].shift(1)) & (tail[left] > tail[right])
    else:
        crossed = (tail[left].shift(1) >= tail[right].shift(1)) & (tail[left] < tail[right])
    dates = tail.index[crossed.fillna(False)]
    return dates[-1] if len(dates) else None


def crossover_events(df: pd.DataFrame, lookback: int = 1) -> dict:
    """Latest fresh bullish EMA-to-EMA cross dates within lookback sessions."""
    return {label: _cross_dates(df, fast, slow, lookback, "bullish")
            for label, (fast, slow) in PAIRS.items()}


def dema_crossover_events(df: pd.DataFrame, lookback: int = 1) -> dict:
    """Latest fresh bullish 50 DEMA vs selected EMA cross dates."""
    return {label: _cross_dates(df, fast, slow, lookback, "bullish")
            for label, (fast, slow) in DEMA_PAIRS.items()}


def price_crossover_events(df: pd.DataFrame, lookback: int = 1, direction: str = "BOTH") -> dict:
    """Latest close-price cross dates above/below DEMA50 and EMA50/100/200."""
    result = {}
    directions = ["bullish", "bearish"] if direction == "BOTH" else [direction.lower()]
    for average_label, average_col in PRICE_AVERAGES.items():
        for side in directions:
            label = f"Price/{average_label} {'ABOVE' if side == 'bullish' else 'BELOW'}"
            result[label] = _cross_dates(df, "Close", average_col, lookback, side)
    return result


def selected_crossover_match(events: dict, selected: list, mode: str) -> tuple[bool, list]:
    matched = [name for name in selected if events.get(name) is not None]
    if not selected:
        return True, []
    qualifies = len(matched) == len(selected) if mode == "ALL" else bool(matched)
    return qualifies, matched
