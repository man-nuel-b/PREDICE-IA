import sys
import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from digital_twin import Asset, Reading, DigitalTwin, normalize_payload

class TwinTests(unittest.TestCase):
    def test_temperature_and_door_alarm(self):
        now = datetime.now(timezone.utc)
        t = DigitalTwin(Asset("A", "Camara", 2, 5))
        t.ingest(Reading("A", now.isoformat(), 8.2, door_open=True))
        self.assertIn("TEMP_OUT_OF_RANGE", t.state(now)["alerts"])
        self.assertIn("DOOR_OPEN", t.state(now)["alerts"])

    def test_stale(self):
        now = datetime.now(timezone.utc)
        t = DigitalTwin(Asset("A", "Camara", 2, 5))
        t.ingest(Reading("A", (now - timedelta(minutes=20)).isoformat(), 4))
        self.assertIn("STALE_TELEMETRY", t.state(now)["alerts"])

    def test_order(self):
        ts = datetime.now(timezone.utc).isoformat()
        t = DigitalTwin(Asset("A", "Camara", 2, 5))
        t.ingest(Reading("A", ts, 4))
        with self.assertRaises(ValueError):
            t.ingest(Reading("A", ts, 3))

    def test_normalization(self):
        reading = normalize_payload({"device":"A","ts":"2026-11-21T15:00:00Z","t":4}, {"asset_id":"device","observed_at":"ts","temp_c":"t"})
        self.assertEqual(reading.temp_c, 4)

if __name__ == "__main__":
    unittest.main()
