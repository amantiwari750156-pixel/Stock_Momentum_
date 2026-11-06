import unittest
import pandas as pd
import numpy as np
from scanner.indicators import add_indicators

class IndicatorTests(unittest.TestCase):
    def test_ema_and_rsi_columns(self):
        idx = pd.date_range("2020-01-01", periods=300, freq="B")
        close = pd.Series(np.linspace(100, 200, 300), index=idx)
        df = pd.DataFrame({"Open":close,"High":close+1,"Low":close-1,"Close":close,"Volume":100000}, index=idx)
        out = add_indicators(df)
        self.assertIn("EMA200", out)
        self.assertAlmostEqual(out["EMA50"].iloc[-1], close.ewm(span=50, adjust=False).mean().iloc[-1], places=8)
        self.assertGreater(out["RSI"].iloc[-1], 50)

if __name__ == "__main__": unittest.main()

class TestDEMA50(unittest.TestCase):
    def test_dema50_matches_double_ema_formula(self):
        import pandas as pd
        import numpy as np
        from scanner.indicators import add_indicators
        idx = pd.date_range("2020-01-01", periods=400)
        close = pd.Series(np.linspace(100, 200, 400), index=idx)
        df = pd.DataFrame({"Open": close, "High": close + 1, "Low": close - 1,
                           "Close": close, "Volume": 1000}, index=idx)
        out = add_indicators(df)
        e1 = close.ewm(span=50, adjust=False, min_periods=50).mean()
        e2 = e1.ewm(span=50, adjust=False, min_periods=50).mean()
        self.assertAlmostEqual(out["DEMA50"].iloc[-1], (2 * e1 - e2).iloc[-1], places=10)
