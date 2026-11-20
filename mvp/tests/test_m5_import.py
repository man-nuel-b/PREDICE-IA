import csv
import json
import tempfile
import unittest
from pathlib import Path
from m5_import import convert

class M5ImportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.calendar = self.root/"calendar.csv"
        self.sales = self.root/"sales_train_validation.csv"
        with self.calendar.open("w", newline="", encoding="utf-8") as f:
            writer=csv.writer(f);writer.writerow(["d","date","wm_yr_wk"])
            for i in range(1,41):
                from datetime import date,timedelta
                writer.writerow([f"d_{i}",(date(2016,1,1)+timedelta(days=i-1)).isoformat(),"100"])
        with self.sales.open("w",newline="",encoding="utf-8") as f:
            writer=csv.writer(f)
            writer.writerow(["item_id","store_id","cat_id"]+[f"d_{i}" for i in range(1,41)])
            writer.writerow(["FOODS_1","CA_1","FOODS"]+[2]*40)
            writer.writerow(["FOODS_2","CA_1","FOODS"]+[0]*40)
    def tearDown(self): self.temp.cleanup()
    def test_converts_only_actual_sales_without_synthetic_waste(self):
        out=self.root/"out"
        report=convert(self.sales,self.calendar,out,products=2,days=20)
        self.assertEqual(report["rows"],20)
        self.assertEqual(report["series"],1)
        self.assertEqual(report["last_day"],"2016-02-09")
        with (out/"sales_m5_historico.csv").open(newline="") as f:
            data=list(csv.DictReader(f))
        self.assertEqual(len(data),20)
        self.assertEqual(data[0]["sku"],"FOODS_1")
        self.assertFalse((out/"waste.csv").exists())
        self.assertFalse((out/"lots.csv").exists())
        self.assertIn("No contiene mermas reales",json.loads((out/"provenance.json").read_text())["notes"][1])
    def test_rejects_invalid_volume(self):
        with self.assertRaises(ValueError):
            convert(self.sales,self.calendar,self.root/"out",products=30,days=1000)
    def test_rejects_invalid_negative_sales(self):
        with self.sales.open("w",newline="") as f:
            writer=csv.writer(f)
            writer.writerow(["item_id","store_id","cat_id"]+[f"d_{i}" for i in range(1,41)])
            writer.writerow(["FOODS_1","CA_1","FOODS"]+[-1]*40)
        with self.assertRaisesRegex(ValueError,"No hay series"):
            convert(self.sales,self.calendar,self.root/"out",products=1,days=20)

if __name__=="__main__":unittest.main()
