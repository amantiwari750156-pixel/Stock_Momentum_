import unittest
import pandas as pd
from scanner.crossover import dema_crossover_events, price_crossover_events


class DemaAndPriceCrossoverTests(unittest.TestCase):
    def test_dema_vs_ema_bullish_cross_is_detected(self):
        idx = pd.date_range("2024-01-01", periods=4)
        df = pd.DataFrame({
            "DEMA50": [8, 9, 11, 12],
            "EMA100": [10, 10, 10, 10],
            "EMA50": [10, 10, 10, 10],
            "EMA200": [10, 10, 10, 10],
        }, index=idx)
        events = dema_crossover_events(df, 2)
        self.assertEqual(events["DEMA50/EMA100"], idx[2])

    def test_price_cross_above_ema_is_detected(self):
        idx = pd.date_range("2024-01-01", periods=4)
        df = pd.DataFrame({
            "Close": [9, 9, 11, 12], "DEMA50": [10]*4,
            "EMA50": [10]*4, "EMA100": [10]*4, "EMA200": [10]*4,
        }, index=idx)
        events = price_crossover_events(df, 2, "BULLISH")
        self.assertEqual(events["Price/EMA50 ABOVE"], idx[2])
        self.assertIsNone(events["Price/EMA50 BELOW"] if "Price/EMA50 BELOW" in events else None)


if __name__ == "__main__":
    unittest.main()
