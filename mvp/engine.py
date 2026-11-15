"""Motor transparente de decisiones de Predice-IA.

No presenta sus cálculos como probabilidades calibradas ni como un modelo de ML
entrenado: aplica estadísticas descriptivas, medias ponderadas y escenarios.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from math import ceil, isfinite, sqrt
from statistics import pstdev
from typing import Any


CONFIDENCE_Z = {"90": 1.282, "95": 1.645, "98": 2.054}
MAX_ROWS = 20_000


class InputError(ValueError):
    """Solicitud inválida sin exponer detalles internos."""


def number(v: Any, field: str, *, positive: bool = False, nonnegative: bool = False) -> float:
    try:
        result = float(v)
    except (TypeError, ValueError, OverflowError):
        raise InputError(f"{field}: número inválido") from None
    if not isfinite(result):
        raise InputError(f"{field}: debe ser finito")
    if positive and result <= 0 or nonnegative and result < 0:
        raise InputError(f"{field}: fuera del rango permitido")
    if abs(result) > 1_000_000_000:
        raise InputError(f"{field}: valor excesivo")
    return result


def parsedate(v: Any, field: str) -> date:
    try:
        d = date.fromisoformat(str(v))
    except (TypeError, ValueError):
        raise InputError(f"{field}: usar AAAA-MM-DD") from None
    return d


def text(v: Any, field: str) -> str:
    if not isinstance(v, str) or not v.strip() or len(v.strip()) > 120:
        raise InputError(f"{field}: texto obligatorio de hasta 120 caracteres")
    return v.strip()


def validate_dataset(kind: str, records: Any) -> list[dict]:
    if kind not in ("lots", "sales", "waste"):
        raise InputError("Tipo de datos desconocido")
    if not isinstance(records, list) or len(records) > MAX_ROWS:
        raise InputError(f"Debe ser una lista con máximo {MAX_ROWS} registros")
    out = []
    for i, row in enumerate(records, 1):
        if not isinstance(row, dict):
            raise InputError(f"Fila {i}: objeto inválido")
        r = dict(row)
        try:
            for field in ("sku", "location"):
                r[field] = text(r.get(field), field)
            if kind == "lots":
                for field in ("code", "name", "category", "unit"):
                    r[field] = text(r.get(field), field)
                for field in ("quantity", "unit_cost", "unit_price"):
                    r[field] = number(r.get(field), field, nonnegative=True)
                r["expires_on"] = parsedate(r.get("expires_on"), "expires_on").isoformat()
                r["manual_daily_sales"] = number(r.get("manual_daily_sales", 0), "manual_daily_sales", nonnegative=True)
                r["shelf_life_days"] = int(number(r.get("shelf_life_days", 7), "shelf_life_days", positive=True))
                if not 1 <= r["shelf_life_days"] <= 730:
                    raise InputError("shelf_life_days: usar 1 a 730")
            elif kind == "sales":
                r["sold_on"] = parsedate(r.get("sold_on"), "sold_on").isoformat()
                r["quantity"] = number(r.get("quantity"), "quantity", nonnegative=True)
                r["unit_price"] = number(r.get("unit_price", 0), "unit_price", nonnegative=True)
            else:
                r["occurred_on"] = parsedate(r.get("occurred_on"), "occurred_on").isoformat()
                r["quantity"] = number(r.get("quantity"), "quantity", nonnegative=True)
                r["unit_cost"] = number(r.get("unit_cost"), "unit_cost", nonnegative=True)
            out.append(r)
        except InputError as exc:
            raise InputError(f"Fila {i}: {exc}") from None
    if kind == "lots":
        codes = [(r["code"], r["location"]) for r in out]
        if len(codes) != len(set(codes)):
            raise InputError("Códigos de lote duplicados en la misma ubicación")
    return out


def demand_metrics(sales: list[dict], sku: str, location: str, today: date) -> dict:
    """Promedios recientes sobre fechas reportadas; faltantes no se asumen ventas cero."""
    totals: dict[date, float] = defaultdict(float)
    for r in sales:
        d = date.fromisoformat(r["sold_on"])
        if r["sku"] == sku and r["location"] == location and today - timedelta(days=55) <= d <= today:
            totals[d] += r["quantity"]
    last28 = {d:v for d,v in totals.items() if d >= today-timedelta(days=27)}
    recent = [v for d,v in last28.items() if d>=today-timedelta(days=6)]
    older = list(last28.values())
    if not older:
        return {"daily": None, "sigma": None, "observed_days": 0, "coverage": 0, "method": "manual", "confidence": "baja"}
    base = sum(older)/len(older)
    rate = .65*(sum(recent)/len(recent))+.35*base if len(recent)>=3 else base
    sigma = pstdev(older) if len(older)>=2 else max(rate*.35, 1.0)
    coverage = round(len(older)/28, 3)
    confidence = "alta" if len(older)>=21 else "media" if len(older)>=10 else "baja"
    return {"daily": round(rate, 3), "sigma": round(sigma, 3), "observed_days":len(older), "coverage":coverage, "method":"media_ponderada", "confidence":confidence}


def simulate(opening: float, order: int, demand: float, cost: float, price: float,
             shelf_life: int, horizon: int, spoilage_factor: float) -> dict:
    available = opening + order
    sold = min(available, demand)
    remainder = max(0.0,available-demand)
    # Conservador: el modelo distingue horizonte menor que vida útil.
    expired = remainder*spoilage_factor if shelf_life <= horizon else 0.0
    unmet = max(0.0,demand-available)
    # Penalización explícita por stock no vendido y capital inmovilizado.
    # La tasa es un supuesto exploratorio, no una tasa financiera real.
    carrying_cost = max(0,remainder-expired)*cost*.03*max(1,horizon)/30
    contribution = sold*(price-cost)-expired*cost-carrying_cost
    return {"order":order, "expected_sales":round(sold,2), "estimated_waste_units":round(expired,2),
            "estimated_waste_cost":round(expired*cost), "unmet_demand":round(unmet,2),
            "carrying_cost_proxy":round(carrying_cost),"capital_in_remaining_stock":round(remainder*cost),
            "contribution_proxy":round(contribution), "end_stock":round(remainder,2)}


def analyze(datasets: dict, settings: dict | None = None, *, today: date | None = None) -> dict:
    settings = settings or {}
    today = today or date.today()
    lots = validate_dataset("lots", datasets.get("lots", []))
    sales = validate_dataset("sales", datasets.get("sales", []))
    waste = validate_dataset("waste", datasets.get("waste", []))
    lead = int(number(settings.get("lead_days", 2), "lead_days", nonnegative=True))
    review = int(number(settings.get("review_days", 7), "review_days", positive=True))
    service = str(settings.get("service", "95"))
    waste_fraction = number(settings.get("spoilage_factor", 1), "spoilage_factor", nonnegative=True)
    if service not in CONFIDENCE_Z or not 0 <= lead <= 90 or not 1 <= review <= 90 or waste_fraction > 1:
        raise InputError("Configuración: rangos no admitidos")
    horizon = lead + review
    if not 1 <= horizon <= 180:
        raise InputError("Horizonte de compra demasiado largo")
    per_sku: dict[tuple[str,str],dict] = {}
    groups: dict[tuple[str,str],list[dict]] = defaultdict(list)
    for row in lots:
        groups[(row["sku"],row["location"])].append(row)
    recommendations=[]; risks=[]; missing=[]; totals={"inventory_value":0.0,"exposure":0.0,"observed_waste_cost":0.0,"potential_waste_units":0.0}
    for r in waste:
        if date.fromisoformat(r["occurred_on"])<=today:
            totals["observed_waste_cost"]+=r["quantity"]*r["unit_cost"]
    for (sku,location),rows in sorted(groups.items()):
        rows.sort(key=lambda r:r["expires_on"]) # FEFO en proyecciones
        m=demand_metrics(sales,sku,location,today)
        if m["daily"] is None:
            reported=[r["manual_daily_sales"] for r in rows]
            daily=round(sum(reported)/len(reported),3)
            missing.append({"sku":sku,"location":location,"reason":"Sin historial diario suficiente; se usa una tasa manual."})
        else:
            daily=m["daily"]
        rate=daily
        remaining_horizon=daily*horizon
        opening=sum(r["quantity"] for r in rows)
        price=sum(r["unit_price"]*r["quantity"] for r in rows)/opening if opening else rows[0]["unit_price"]
        cost=sum(r["unit_cost"]*r["quantity"] for r in rows)/opening if opening else rows[0]["unit_cost"]
        shelf=min(r["shelf_life_days"] for r in rows)
        z=CONFIDENCE_Z[service]
        sigma=m["sigma"] if m["sigma"] is not None else max(rate*.35,1)
        safety=z*sigma*sqrt(horizon) if m["confidence"]!="baja" else 0.0
        # Usable inventory at review horizon: count only lots not expired at expected delivery.
        live_at_delivery=sum(r["quantity"] for r in rows if date.fromisoformat(r["expires_on"])>=today+timedelta(days=lead))
        usable_at_delivery=max(0.0,live_at_delivery-rate*lead)
        base_order=max(0,ceil(rate*horizon+safety-usable_at_delivery))
        # Cap conservador: no recomendar más de lo esperable durante la vida útil.
        max_perishable=max(0,ceil(rate*min(horizon,shelf)+safety-usable_at_delivery))
        suggested=min(base_order,max_perishable)
        if m["confidence"]=="baja":
            # No automatizar compras con información insuficiente.
            recommendation_status="revisar_manual"
        else:
            recommendation_status="sugerencia"
        # FEFO: la demanda acumulada se asigna una sola vez entre lotes.
        # Un lote posterior no reutiliza las ventas ya asignadas a otro anterior.
        allocated_sales=0.0
        for lot in rows:
            days_to_expiry=(date.fromisoformat(lot["expires_on"])-today).days
            days_available=max(0,days_to_expiry)
            cumulative_capacity=rate*days_available
            potential_sale=min(lot["quantity"],max(0.0,cumulative_capacity-allocated_sales))
            allocated_sales+=potential_sale
            excess=max(0,lot["quantity"]-potential_sale)
            loss=round(excess*lot["unit_cost"])
            totals["inventory_value"]+=lot["quantity"]*lot["unit_cost"]
            totals["exposure"]+=loss
            totals["potential_waste_units"]+=excess
            if loss>0:
                risks.append({"code":lot["code"],"sku":sku,"name":lot["name"],"location":location,
                              "days_to_expiry":days_to_expiry,"quantity":lot["quantity"],"potential_excess":round(excess,2),
                              "cost_exposure":loss,"priority":"alta" if days_to_expiry<=3 else "media" if days_to_expiry<=7 else "baja",
                              "reason":"Stock potencial no vendido antes del vencimiento con el ritmo observado o manual."})
        options=[simulate(usable_at_delivery,n,remaining_horizon,cost,price,shelf,horizon,waste_fraction)
                for n in sorted(set([0,suggested,max(0,round(base_order*1.2))]))]
        # Optimización simple por máximo proxy, informando la incertidumbre.
        best=max(options,key=lambda x:(x["contribution_proxy"],-x["estimated_waste_cost"],-x["order"]))
        recommendations.append({"sku":sku,"location":location,"name":rows[0]["name"],"unit":rows[0]["unit"],
          "daily_demand":rate,"daily_sigma":sigma,"coverage":m["coverage"],"confidence":m["confidence"],
          "method":m["method"] if m["daily"] is not None else "estimación_manual",
          "current_stock":round(opening,2),"usable_at_delivery":round(usable_at_delivery,2),
          "horizon_days":horizon,"service_level":service,"safety_stock":round(safety,2),
          "recommended_order":suggested,"decision_status":recommendation_status,
          "reason":f"Demanda estimada {rate:.2f}/día × {horizon} días, stock utilizable {usable_at_delivery:.2f}, seguridad {safety:.2f}. No automatizar sin revisión.",
          "scenarios":options,"highest_contribution_scenario":best,"unit_cost":round(cost,2),"unit_price":round(price,2)})
    risks.sort(key=lambda x:(-x["cost_exposure"],x["days_to_expiry"]))
    recommendations.sort(key=lambda x:(x["decision_status"]!="revisar_manual",-x["recommended_order"]))
    return {"as_of":today.isoformat(),"settings":{"lead_days":lead,"review_days":review,"service":service,"spoilage_factor":waste_fraction},
      "kpis":{k:round(v,2) for k,v in totals.items()}|{"sku_locations":len(recommendations),"at_risk_lots":len(risks),"recorded_sales":len(sales),"recorded_waste_events":len(waste)},
      "recommendations":recommendations,"risks":risks,"data_gaps":missing,
      "disclaimer":"Cálculo exploratorio, NO IA entrenada ni probabilidad calibrada. Exposición potencial no equivale a merma observada ni ahorro conseguido. Revisar inocuidad y obligaciones legales antes de redistribuir o descontar."}
