"""Evaluación retrospectiva de demanda, sin fuga de información futura.

No es entrenamiento de ML: mide el error de la heurística actual en fechas
históricas, sin asumir que días sin registros son ventas cero.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta
from math import isfinite
from statistics import mean

from engine import demand_metrics, validate_dataset


def backtest_sales(sales: list[dict], *, minimum_train_days: int = 10,
                   minimum_test_days: int = 5, horizon_days: int = 1) -> dict:
    """Evalúa pronóstico diario con origen móvil para cada SKU y ubicación.

    Sólo compara fechas efectivamente registradas. Para evitar fuga, las
    observaciones del propio día y posteriores quedan fuera del entrenamiento.
    Un pronóstico de horizonte >1 exige verificar un registro para ese día y
    no pretende simular una predicción multietapa calibrada.
    """
    if not isinstance(minimum_train_days, int) or not 3 <= minimum_train_days <= 180:
        raise ValueError("minimum_train_days debe estar entre 3 y 180")
    if not isinstance(minimum_test_days, int) or not 1 <= minimum_test_days <= 180:
        raise ValueError("minimum_test_days debe estar entre 1 y 180")
    if not isinstance(horizon_days, int) or horizon_days != 1:
        raise ValueError("Versión inicial solo admite horizonte diario de 1 día")
    rows = validate_dataset("sales", sales)
    groups = defaultdict(lambda: defaultdict(float))
    for row in rows:
        groups[(row["sku"], row["location"])][date.fromisoformat(row["sold_on"])] += row["quantity"]

    results = []
    for (sku, location), history in sorted(groups.items()):
        days = sorted(history)
        # Requiere registros históricos suficientes, no continuidad inventada.
        if len(days) < minimum_train_days + minimum_test_days:
            results.append({"sku": sku, "location": location, "status": "insuficiente",
                            "observed_days": len(days), "evaluated_days": 0})
            continue
        scored = []
        for target in days:
            origin = target - timedelta(days=1)
            prior = [d for d in days if d <= origin]
            if len(prior) < minimum_train_days:
                continue
            training = [{"sku": sku, "location": location, "sold_on": d.isoformat(),
                         "quantity": history[d]} for d in prior
                        if d >= origin - timedelta(days=27)]
            if len(training) < minimum_train_days:
                continue
            metrics = demand_metrics(training, sku, location, origin)
            if metrics["daily"] is None:
                continue
            actual = history[target]
            prediction = metrics["daily"]
            if not isfinite(prediction):
                continue
            scored.append((actual, prediction))
        if len(scored) < minimum_test_days:
            results.append({"sku": sku, "location": location, "status": "insuficiente",
                            "observed_days": len(days), "evaluated_days": len(scored)})
            continue
        absolute_errors = [abs(actual - prediction) for actual, prediction in scored]
        actual_total = sum(a for a, _ in scored)
        mae = mean(absolute_errors)
        bias = mean(p - a for a, p in scored)
        wape = sum(absolute_errors) / actual_total * 100 if actual_total > 0 else None
        results.append({"sku": sku, "location": location, "status": "evaluado",
                        "observed_days": len(days), "evaluated_days": len(scored),
                        "mae_units": round(mae, 3), "bias_units": round(bias, 3),
                        "wape_percent": round(wape, 2) if wape is not None else None,
                        "actual_units": round(actual_total, 3),
                        "absolute_error_units": round(sum(absolute_errors), 3)})
    evaluated = [r for r in results if r["status"] == "evaluado"]
    total_actual = sum(r["actual_units"] for r in evaluated)
    total_error = sum(r["absolute_error_units"] for r in evaluated)
    return {
        "method": "walk_forward_observed_dates",
        "horizon_days": 1,
        "minimum_train_days": minimum_train_days,
        "minimum_test_days": minimum_test_days,
        "evaluated_series": len(evaluated),
        "insufficient_series": len(results) - len(evaluated),
        "micro_wape_percent": round(total_error / total_actual * 100, 2)
                              if total_actual > 0 else None,
        "series": results,
        "warning": ("Backtesting exploratorio de la heurística, no validación de IA ni "
                    "precisión futura garantizada. Días faltantes no son ceros; "
                    "el sesgo por días no reportados puede afectar las métricas.")
    }
