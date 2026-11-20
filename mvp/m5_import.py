"""Convert user-downloaded Walmart M5 sales into Predice-IA's CSV contract.

No third-party packages. M5 is a historical DEMAND benchmark, not observed waste.
Never fabricate waste or mix past M5 observations with current-dated pilot results.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

MAX_SALES = 20000
MAX_PRODUCTS = 30

def load_calendar(path: Path):
    mapped = {}
    with path.open(newline="", encoding="utf-8-sig") as source:
        for row in csv.DictReader(source):
            key = row.get("d")
            if not key or not key.startswith("d_"):
                continue
            mapped[key] = (date.fromisoformat(row["date"]), row.get("wm_yr_wk", ""))
    if not mapped:
        raise ValueError("calendar.csv no contiene días d_N válidos")
    return mapped

def load_prices(path: Path | None, targets: set[tuple[str,str]]):
    if path is None:
        return {}
    prices = {}
    with path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        required = {"store_id", "item_id", "wm_yr_wk", "sell_price"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("sell_prices.csv: faltan columnas")
        for row in reader:
            key = (row["item_id"], row["store_id"])
            if key not in targets:
                continue
            try:
                value = float(row["sell_price"])
            except (ValueError, TypeError):
                continue
            if math.isfinite(value) and value >= 0:
                prices[(key[0],key[1],row["wm_yr_wk"])] = value
    return prices

def selected_series(sales_path: Path, max_products: int):
    selected = []
    with sales_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if not {"item_id", "store_id", "cat_id"}.issubset(reader.fieldnames or []):
            raise ValueError("M5 sales: faltan item_id, store_id o cat_id")
        days = [x for x in (reader.fieldnames or []) if x.startswith("d_") and x[2:].isdigit()]
        if not days:
            raise ValueError("M5 sales: faltan columnas de demanda d_1, d_2, ...")
        days.sort(key=lambda x: int(x.split("_")[1]))
        window = days[-365:]
        for row in reader:
            try:
                units = [float(row.get(k, "")) for k in window]
            except (ValueError, TypeError):
                continue
            if any(not math.isfinite(q) or q < 0 for q in units):
                continue
            activity = sum(units[-56:])
            if activity <= 0:
                continue
            selected.append((activity, row["item_id"], row["store_id"], row["cat_id"], window, units))
    selected.sort(key=lambda x: (-x[0],x[1],x[2]))
    return selected[:max_products]

def convert(sales_path: Path, calendar_path: Path, destination: Path,
            prices_path: Path | None = None, products: int = 12, days: int = 365):
    if not 1 <= products <= MAX_PRODUCTS:
        raise ValueError("products debe ser 1..30")
    if not 15 <= days <= 365 or products * days > MAX_SALES:
        raise ValueError("Rango excede 20.000 filas o días fuera de 15..365")
    calendar = load_calendar(calendar_path)
    chosen = selected_series(sales_path, products)
    if not chosen:
        raise ValueError("No hay series con demanda positiva reciente")
    keys = {(item,store) for _,item,store,_,_,_ in chosen}
    prices = load_prices(prices_path, keys)
    destination.mkdir(parents=True, exist_ok=True)
    rows = []
    for _,item,store,cat,window,units in chosen:
        for key,qty in zip(window[-days:],units[-days:]):
            if key not in calendar:
                raise ValueError("Falta " + key + " en calendar.csv")
            day,week = calendar[key]
            price = prices.get((item,store,week), 0)
            rows.append({"sku":item,"location":store,"sold_on":day.isoformat(),
                         "quantity":qty,"unit_price":price})
    # Validation against the EXACT existing MVP contract.
    from engine import validate_dataset
    rows = validate_dataset("sales", rows)
    filename = destination / "sales_m5_historico.csv"
    with filename.open("w",newline="",encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=("sku","location","sold_on","quantity","unit_price"))
        writer.writeheader()
        writer.writerows(rows)
    # No lots or waste created; cannot infer expired goods from sales alone.
    report = {
        "source": "M5 Forecasting Accuracy (Walmart), historical observations",
        "series":len(chosen),
        "rows":len(rows),
        "first_day":min(x["sold_on"] for x in rows),
        "last_day":max(x["sold_on"] for x in rows),
        "price_currency":"USD (not CLP)" if prices_path else "unknown",
        "prices_available": bool(prices_path),
        "notes":[
          "Ventas históricas reales del benchmark, no ventas de una empresa chilena.",
          "No contiene mermas reales ni fechas de vencimiento por lote.",
          "No importar precios en USD como CLP; usar exclusivamente cantidades para benchmark.",
          "Importación CSV del MVP reemplaza el conjunto previo del tipo ventas.",
          "No subir datos originales completos al repositorio: revisar condiciones de uso de la fuente."
        ]
    }
    (destination/"provenance.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    return report

def main():
    parser=argparse.ArgumentParser(description="Convertidor de M5 a ventas CSV de Predice-IA")
    parser.add_argument("--sales",type=Path,required=True,help="sales_train_validation.csv")
    parser.add_argument("--calendar",type=Path,required=True,help="calendar.csv")
    parser.add_argument("--prices",type=Path,help="sell_prices.csv (opcional, precios USD)")
    parser.add_argument("--out",type=Path,default=Path(".local/m5"))
    parser.add_argument("--products",type=int,default=12)
    parser.add_argument("--days",type=int,default=365)
    args=parser.parse_args()
    report=convert(args.sales,args.calendar,args.out,args.prices,args.products,args.days)
    print(json.dumps(report,indent=2,ensure_ascii=False))

if __name__ == "__main__":
    main()
