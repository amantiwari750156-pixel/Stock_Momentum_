import unittest
import pandas as pd
from scanner.crossover import crossover_events, selected_crossover_match

class CrossoverTests(unittest.TestCase):
    def test_fresh_cross_and_lookback(self):
        idx = pd.date_range("2024-01-01", periods=4)
        df = pd.DataFrame({"EMA50":[1,1,3,4],"EMA100":[2,2,2,2],"EMA200":[3,3,3,3]}, index=idx)
        self.assertEqual(crossover_events(df, 2)["50/100"], idx[2])
        self.assertIsNone(crossover_events(df, 1)["50/100"])
    def test_any_all(self):
        events = {"50/100": pd.Timestamp("2024-01-01"), "50/200": None}
        self.assertTrue(selected_crossover_match(events, ["50/100","50/200"], "ANY")[0])
        self.assertFalse(selected_crossover_match(events, ["50/100","50/200"], "ALL")[0])

if __name__ == "__main__": unittest.main()
