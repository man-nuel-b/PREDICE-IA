import unittest
from datetime import date,timedelta
from engine import analyze,validate_dataset,InputError,simulate
from demo import sample_data

NOW=date(2026,11,15)

class EngineTests(unittest.TestCase):
    def test_demo_is_analyzable(self):
        r=analyze(sample_data(NOW),today=NOW)
        self.assertEqual(r['kpis']['sku_locations'],5)
        self.assertEqual(len(r['recommendations']),5)
        self.assertTrue(r['risks'])
        self.assertTrue(all('reason' in p and 'scenarios' in p for p in r['recommendations']))
    def test_real_vs_potential_loss_is_distinct(self):
        d=sample_data(NOW);r=analyze(d,today=NOW)
        self.assertNotEqual(r['kpis']['observed_waste_cost'],r['kpis']['exposure'])
        self.assertGreater(r['kpis']['observed_waste_cost'],0)
    def test_manual_fallback_warning(self):
        d=sample_data(NOW);d['sales']=[]
        r=analyze(d,today=NOW)
        self.assertEqual(len(r['data_gaps']),5)
        self.assertTrue(all(p['decision_status']=='revisar_manual' for p in r['recommendations']))
    def test_prevent_duplicate_lots(self):
        d=sample_data(NOW)
        with self.assertRaisesRegex(InputError,'duplicados'):
            validate_dataset('lots',d['lots']+[dict(d['lots'][0])])
    def test_invalid_sales_are_rejected(self):
        d=sample_data(NOW)
        r=d['sales'][0].copy();r['quantity']=-2
        with self.assertRaises(InputError):validate_dataset('sales',[r])
        r['quantity']='NaN'
        with self.assertRaises(InputError):validate_dataset('sales',[r])
    def test_invalid_calendar_is_rejected(self):
        d=sample_data(NOW);d['lots'][0]['expires_on']='2026-02-30'
        with self.assertRaises(InputError):analyze(d,today=NOW)
    def test_multiple_lots_do_not_double_count_sales(self):
        d=sample_data(NOW)
        first=d['lots'][0]
        first.update({'quantity':100,'expires_on':(NOW+timedelta(days=5)).isoformat(), 'manual_daily_sales':10})
        duplicate=first.copy();duplicate.update({'code':'DEMO-OTHER','quantity':100})
        d['lots']=[first,duplicate];d['sales']=[];d['waste']=[]
        r=analyze(d,today=NOW)
        self.assertAlmostEqual(r['kpis']['potential_waste_units'],150)
        self.assertAlmostEqual(sum(x['potential_excess'] for x in r['risks']),150)
    def test_scenarios_do_not_claim_sales_over_demand(self):
        r=simulate(100,100,25,500,900,5,9,1)
        self.assertEqual(r['expected_sales'],25)
        self.assertEqual(r['estimated_waste_units'],175)
        self.assertEqual(r['unmet_demand'],0)
    def test_settings_limits(self):
        d=sample_data(NOW)
        with self.assertRaises(InputError):analyze(d,{'lead_days':-1},today=NOW)
        with self.assertRaises(InputError):analyze(d,{'service':'99'},today=NOW)
        with self.assertRaises(InputError):analyze(d,{'spoilage_factor':2},today=NOW)
    def test_report_only_uses_data_until_today(self):
        d=sample_data(NOW)
        d['waste'].append({'sku':'X','location':'Y','occurred_on':'2028-01-01','quantity':9999,'unit_cost':1000})
        r=analyze(d,today=NOW)
        self.assertLess(r['kpis']['observed_waste_cost'],1000000)

if __name__=='__main__':unittest.main()
