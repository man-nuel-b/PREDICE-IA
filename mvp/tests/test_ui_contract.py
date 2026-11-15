"""Pruebas de contrato visual para impedir regresiones al adoptar nuevas interfaces."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

WEB = Path(__file__).resolve().parent.parent / "web"


class IdParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if "id" in values:
            self.ids.add(values["id"])


class InterfaceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (WEB / "index.html").read_text(encoding="utf-8")
        cls.js = (WEB / "app.js").read_text(encoding="utf-8")
        cls.css = (WEB / "styles.css").read_text(encoding="utf-8")

    def test_required_elements_for_engine(self):
        parser = IdParser()
        parser.feed(self.html)
        expected = {"alert", "kpis", "risk-bars", "featured",
                    "recommendations-body", "risks-body", "scenario-panel",
                    "quality", "settings-form", "kind", "csv-file",
                    "import-button", "reset-button", "motor-status",
                    "motor-status-dot"}
        self.assertFalse(expected - parser.ids)

    def test_real_engine_endpoints_remain_connected(self):
        for endpoint in ("/api/data", "/api/analyze", "/api/import", "/api/reset"):
            with self.subTest(endpoint=endpoint):
                self.assertIn(endpoint, self.js)
        self.assertIn("renderScenario", self.js)
        self.assertIn("parseCSV", self.js)

    def test_no_fictitious_confidence_or_unconnected_prediction(self):
        self.assertNotIn("98.4% Confianza", self.html)
        self.assertNotIn("prediction-form", self.html)
        self.assertNotIn("basePrediction", self.js)
        self.assertIn("motor-status", self.js)

    def test_dark_theme_and_responsiveness(self):
        self.assertIn("Interfaz de alto contraste adaptada", self.css)
        self.assertIn("--light:#0f172a", self.css)
        self.assertIn("@media(max-width:450px)", self.css)

    def test_advanced_analytics_interface(self):
        parser = IdParser()
        parser.feed(self.html)
        expected = {"advanced", "advanced-period", "advanced-location",
                    "advanced-export", "advanced-kpis", "advanced-waste-trend",
                    "advanced-sales-trend", "advanced-categories", "advanced-pareto",
                    "advanced-demand", "advanced-insights"}
        self.assertFalse(expected - parser.ids)
        self.assertIn('/advanced-analytics.js', self.html)
        self.assertIn('/advanced-ui.js', self.html)
        self.assertIn('PrediceAdvancedUI', self.js)


if __name__ == "__main__":
    unittest.main()
