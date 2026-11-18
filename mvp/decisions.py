"""Inteligencia preventiva explicable. No ejecuta compras ni cambios de precio."""
from __future__ import annotations
from collections import defaultdict
from datetime import date, timedelta
from math import ceil
from statistics import mean
from backtesting import backtest_sales
from engine import analyze, validate_dataset


def prevention_report(datasets: dict, settings: dict | None = None, *, today: date | None = None) -> dict:
    today = today or date.today()
    base = analyze(datasets, settings, today=today)
    lots = validate_dataset("lots", datasets.get("lots", []))
    sales = validate_dataset("sales", datasets.get("sales", []))
    history = backtest_sales([x for x in sales if date.fromisoformat(x["sold_on"]) <= today])
    score = {(r["sku"], r["location"]): r for r in history["series"]}
    rec = {(r["sku"], r["location"]): r for r in base["recommendations"]}
    actions = []
    for risk in base["risks"]:
        item = next((l for l in lots if l["code"] == risk["code"] and l["location"] == risk["location"]), None)
        if item is None:
            continue
        days = risk["days_to_expiry"]
        exposed = float(risk["cost_exposure"])
        potential = float(risk["potential_excess"])
        price = float(item["unit_price"])
        cost = float(item["unit_cost"])
        s = score.get((risk["sku"], risk["location"]), {})
        unreliable = s.get("status") != "evaluado" or (s.get("wape_percent") is not None and s["wape_percent"] > 35)
        # Los descuentos son escenarios, no precios sugeridos sin verificar márgenes e inocuidad.
        discount = 0.15 if days >= 2 else 0.25
        discount_price = round(price * (1 - discount))
        incremental_margin = round(potential * max(0, discount_price - cost))
        candidate = "Revisar rebaja controlada" if discount_price > cost else "Revisar traslado o reducción de futuras compras"
        if days < 0:
            candidate = "Retirar de oferta y validar disposición según normas aplicables"
        elif days == 0:
            candidate = "Revisión urgente de inocuidad, trazabilidad y disposición"
        elif unreliable:
            candidate = "Confirmar inventario, ventas y fecha antes de decidir"
        actions.append({
            "sku": risk["sku"], "location": risk["location"], "lot_code": risk["code"],
            "name": risk["name"], "days_to_expiry": days,
            "exposure_clp": round(exposed), "potential_excess": round(potential, 2),
            "action": candidate, "priority": "critica" if days <= 1 else "alta" if days <= 3 else "media",
            "suggested_discount_scenario_pct": round(discount * 100) if days > 0 else None,
            "discounted_price_scenario_clp": discount_price if days > 0 else None,
            "gross_margin_if_all_excess_sold_clp": incremental_margin if days > 0 else None,
            "needs_manual_review": True,
            "rationale": "Exposición estimada al costo; no es merma confirmada. Validar condiciones sanitarias, factibilidad comercial y costos adicionales."
        })
    actions.sort(key=lambda r: ({"critica": 0, "alta": 1, "media": 2}[r["priority"]], -r["exposure_clp"]))
    purchases = []
    for r in base["recommendations"]:
        bt = score.get((r["sku"], r["location"]), {})
        low = r["decision_status"] == "revisar_manual"
        unreliable = bt.get("status") != "evaluado" or (bt.get("wape_percent") is not None and bt["wape_percent"] > 35)
        status = "revisar_manual" if low or unreliable else "evaluacion_humana"
        scenarios = sorted(r["scenarios"], key=lambda s: s["order"])
        purchases.append({
            "sku": r["sku"], "location": r["location"], "name": r["name"], "unit": r["unit"],
            "recommended_order": r["recommended_order"],
            "daily_demand": r["daily_demand"],
            "decision_status": status, "historic_wape_pct": bt.get("wape_percent"),
            "evaluated_days": bt.get("evaluated_days", 0),
            "reason": "Historial no validado o error elevado: revisar antes de comprar." if status == "revisar_manual" else "Historial evaluado: comparar escenarios y aprobar manualmente.",
            "scenarios": scenarios
        })
    gaps = []
    for r in purchases:
        if r["historic_wape_pct"] is None:
            gaps.append({"sku": r["sku"], "location": r["location"], "reason": "No hay suficientes fechas para medir error histórico."})
    return {
        "as_of": today.isoformat(), "mode": "decision_support_only",
        "backtesting": history, "purchases": purchases, "actions": actions,
        "data_quality": {"untested_series": len(gaps), "issues": gaps,
          "warning": "Ventas observadas pueden subestimar demanda cuando hay quiebres de stock; se necesitan registros de disponibilidad para corregirlo."},
        "limitations": ["Sin ML entrenado ni precisión garantizada", "No equivale a utilidad ni ahorro comprobado",
                        "Descuentos, recuperación y disposición exigen validación humana y sanitaria",
                        "No genera órdenes de compra ni afecta sistemas externos"]
    }
