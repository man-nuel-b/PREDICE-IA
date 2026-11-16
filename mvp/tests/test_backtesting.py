import unittest
from datetime import date, timedelta
from backtesting import backtest_sales


class BacktestingTests(unittest.TestCase):
    def make_sales(self, values):
        start = date(2026, 9, 1)
        return [{"sku": "A", "location": "Temuco",
                 "sold_on": (start + timedelta(days=i)).isoformat(),
                 "quantity": v} for i, v in enumerate(values)]

    def test_constant_demand_has_zero_error(self):
        report = backtest_sales(self.make_sales([10] * 40))
        self.assertEqual(report["evaluated_series"], 1)
        self.assertEqual(report["series"][0]["mae_units"], 0)
        self.assertEqual(report["micro_wape_percent"], 0)

    def test_insufficient_history_is_explicit(self):
        report = backtest_sales(self.make_sales([4] * 8))
        self.assertEqual(report["evaluated_series"], 0)
        self.assertEqual(report["series"][0]["status"], "insuficiente")

    def test_future_information_does_not_leak_to_past(self):
        base = self.make_sales([10] * 40)
        altered = [dict(r) for r in base]
        altered[-1]["quantity"] = 100000
        a = backtest_sales(base)["series"][0]
        b = backtest_sales(altered)["series"][0]
        # En el último día, la predicción sólo depende de los días anteriores.
        self.assertAlmostEqual(b["absolute_error_units"] - a["absolute_error_units"], 99990, places=2)

    def test_rejects_invalid_horizon_and_negative_sales(self):
        with self.assertRaises(ValueError):
            backtest_sales(self.make_sales([1] * 40), horizon_days=3)
        rows = self.make_sales([1] * 40)
        rows[0]["quantity"] = -2
        with self.assertRaises(ValueError):
            backtest_sales(rows)


if __name__ == "__main__":
    unittest.main()
