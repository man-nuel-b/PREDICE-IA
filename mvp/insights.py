"""Diagnósticos explicables para Merma IA 360. No ejecuta acciones externas."""
from __future__ import annotations
from collections import defaultdict
from datetime import date, timedelta
from engine import analyze, validate_dataset

def insight_report(datasets: dict, *, today: date | None = None) -> dict:
    """Genera indicadores de calidad, Pareto, alertas y escenarios comerciales.

    Las causas son hipótesis descriptivas, no inferencias causales. No hay ML entrenado.
    """
    today = today or date.today()
    base = analyze(datasets, today=today)
    lots = validate_dataset("lots", datasets.get("lots", []))
    waste = validate_dataset("waste", datasets.get("waste", []))
    risks = base["risks"]
    exposure = sum(float(r["cost_exposure"]) for r in risks)
    by_category = defaultdict(float)
    by_location = defaultdict(float)
    by_sku = defaultdict(float)
    waste_by_sku = defaultdict(float)
    lot_index = {(r["code"], r["location"]): r for r in lots}
    for r in risks:
        lot = lot_index.get((r["code"], r["location"]))
        if not lot:
            continue
        value = float(r["cost_exposure"])
        by_category[lot["category"]] += value
        by_location[r["location"]] += value
        by_sku[(r["sku"], r["location"])] += value
    for w in waste:
        if date.fromisoformat(w["occurred_on"]) <= today:
            waste_by_sku[(w["sku"], w["location"])] += w["quantity"] * w["unit_cost"]

    ranked = sorted(by_sku.items(), key=lambda x: -x[1])
    pareto = []
    cumulative = 0.0
    for (sku, location), value in ranked:
        cumulative += value
        pareto.append({"sku": sku, "location": location, "exposure_clp": round(value),
                       "cumulative_share_pct": round(100 * cumulative / exposure, 1) if exposure else 0})

    diagnostics = []
    for r in base["recommendations"]:
        key = (r["sku"], r["location"])
        reasons = []
        if r["coverage"] < 0.36:
            reasons.append("Historial de ventas insuficiente: validar datos antes de decidir.")
        if by_sku.get(key, 0) > 0:
            reasons.append("Inventario estimado no vendible antes de vencimiento: revisar FEFO, compras y promociones.")
        if waste_by_sku.get(key, 0) > 0:
            reasons.append("Existen eventos de merma observada: verificar clasificación de motivos en origen.")
        if r["recommended_order"] > 0:
            reasons.append("Revisar reposición sugerida y plazos de suministro con el responsable.")
        diagnostics.append({"sku": key[0], "location": key[1], "hypotheses": reasons,
                            "observed_waste_clp": round(waste_by_sku.get(key, 0)),
                            "exposure_clp": round(by_sku.get(key, 0)),
                            "requires_human_review": True})

    price_scenarios = []
    for risk in risks:
        lot = lot_index.get((risk["code"], risk["location"]))
        if not lot:
            continue
        days = risk["days_to_expiry"]
        cost = float(lot["unit_cost"])
        price = float(lot["unit_price"])
        if days <= 0 or price <= cost or cost <= 0:
            continue
        alternatives = []
        for pct in (10, 15, 20):
            discounted = round(price * (1-pct/100), 2)
            margin = round(discounted-cost, 2)
            alternatives.append({"discount_pct": pct, "price_clp": discounted,
                                 "unit_margin_clp": margin,
                                 "meets_unit_cost_floor": margin >= 0,
                                 "maximum_revenue_if_all_excess_sells_clp":
                                 round(discounted * risk["potential_excess"])})
        price_scenarios.append({"lot_code":risk["code"], "sku":risk["sku"],
                                "location":risk["location"], "days_to_expiry":days,
                                "scenarios":alternatives, "manual_approval_required":True})

    alerts = []
    for r in risks:
        if r["days_to_expiry"] <= 3:
            alerts.append({"lot_code":r["code"],"location":r["location"],
                           "severity":"critica" if r["days_to_expiry"] <= 1 else "alta",
                           "message":"Revisar fecha, condiciones del lote y alternativas permitidas.",
                           "external_notification_sent":False})
    return {
        "as_of":today.isoformat(), "mode":"local_decision_support",
        "exposure_by_category":[{"category":k,"clp":round(v)} for k,v in sorted(by_category.items(),key=lambda x:-x[1])],
        "exposure_by_location":[{"location":k,"clp":round(v)} for k,v in sorted(by_location.items(),key=lambda x:-x[1])],
        "pareto":pareto,"diagnostics":diagnostics,"price_scenarios":price_scenarios,
        "alerts":alerts,
        "limitations":["Hipótesis no causales","Sin IA entrenada ni integración externa",
                       "Escenarios no predicen conversión de promociones",
                       "No se recomiendan ventas de productos vencidos",
                       "Sin proveedores ni motivos de merma en el esquema de entrada"]
    }
