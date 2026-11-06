import unittest
import pandas as pd
from scanner.consolidation import consolidation_metrics

class ConsolidationTests(unittest.TestCase):
    def test_range(self):
        idx = pd.date_range("2024-01-01", periods=100)
        df = pd.DataFrame({"High":[110]*100,"Low":[90]*100,"Close":[100]*100}, index=idx)
        m = consolidation_metrics(df, "100 trading days")
        self.assertAlmostEqual(m["Consolidation Range %"], 20.0)
        self.assertAlmostEqual(m["Distance from High %"], 10/110*100)

if __name__ == "__main__": unittest.main()
