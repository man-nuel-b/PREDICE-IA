import unittest
from pathlib import Path
from server import ASSETS

ROOT=Path(__file__).resolve().parents[1]
class InsightsWiringTests(unittest.TestCase):
 def test_insights_static_assets_routed(self):
  self.assertIn('/insights-ui.js', ASSETS)
  self.assertTrue((ROOT/'web'/'insights-ui.js').exists())
 def test_dashboard_includes_insights_anchors(self):
  page=(ROOT/'web'/'index.html').read_text(encoding='utf-8')
  for fragment in ['id="insights"','id="insights-categories"','id="insights-pareto"','id="insights-diagnostics"','id="insights-prices"','id="insights-alerts"','src="/insights-ui.js"']:
   self.assertIn(fragment,page)
 def test_js_requests_existing_insights_api(self):
  js=(ROOT/'web'/'insights-ui.js').read_text(encoding='utf-8')
  self.assertIn("fetch('/api/insights'",js)
  self.assertIn("'predice:data-updated'",js)
 def test_separate_database_by_design(self):
  sql=(ROOT/'docs'/'MERMA_MULTIEMPRESA_SCHEMA.sql').read_text(encoding='utf-8')
  self.assertIn('enable row level security',sql)
  self.assertIn('organization_id',sql)
  self.assertNotIn('timeless_',sql.lower())
if __name__=='__main__': unittest.main()
