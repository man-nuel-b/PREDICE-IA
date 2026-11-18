import unittest
from datetime import date
from demo import sample_data
from decisions import prevention_report

class DecisionsTests(unittest.TestCase):
    def test_demo_returns_actions_and_backtesting(self):
        d = sample_data(date(2026,11,18))
        r = prevention_report(d, today=date(2026,11,18))
        self.assertEqual(r["mode"], "decision_support_only")
        self.assertTrue(r["purchases"])
        self.assertTrue(r["actions"])
        self.assertGreater(r["backtesting"]["evaluated_series"], 0)
        self.assertTrue(all(a["needs_manual_review"] for a in r["actions"]))
    def test_no_training_data_needs_review(self):
        d = sample_data(date(2026,11,18)); d["sales"]=[]
        r = prevention_report(d, today=date(2026,11,18))
        self.assertTrue(all(p["decision_status"]=="revisar_manual" for p in r["purchases"]))
    def test_expired_lot_not_discounted(self):
        d=sample_data(date(2026,11,18))
        d["lots"][0]["expires_on"]="2026-11-17"
        r=prevention_report(d,today=date(2026,11,18))
        a=next(x for x in r["actions"] if x["lot_code"]==d["lots"][0]["code"])
        self.assertIsNone(a["suggested_discount_scenario_pct"])
        self.assertIn("Retirar",a["action"])
if __name__=="__main__": unittest.main()
