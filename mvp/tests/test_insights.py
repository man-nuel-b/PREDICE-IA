import unittest
from datetime import date, timedelta
from demo import sample_data
from insights import insight_report

TODAY=date(2026,11,18)

class InsightTests(unittest.TestCase):
    def test_report_groups_and_pareto(self):
        result=insight_report(sample_data(TODAY),today=TODAY)
        self.assertEqual(result["mode"],"local_decision_support")
        self.assertTrue(result["diagnostics"])
        if result["pareto"]:
            self.assertAlmostEqual(result["pareto"][-1]["cumulative_share_pct"],100,places=1)
    def test_never_discount_expired_products(self):
        data=sample_data(TODAY)
        data["lots"][0]["expires_on"]=(TODAY-timedelta(days=1)).isoformat()
        result=insight_report(data,today=TODAY)
        expired=data["lots"][0]["code"]
        self.assertFalse(any(x["lot_code"]==expired for x in result["price_scenarios"]))
    def test_zero_risk_has_valid_pareto(self):
        data=sample_data(TODAY)
        data["lots"]=[]
        self.assertEqual(insight_report(data,today=TODAY)["pareto"],[])

if __name__=="__main__": unittest.main()
