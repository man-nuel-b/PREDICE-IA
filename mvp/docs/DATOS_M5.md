# Datos públicos para Merma IA 360

## Fuente: M5 Forecasting Accuracy

Descarga **legalmente bajo las condiciones de la fuente** los archivos `sales_train_validation.csv` y `calendar.csv` (opcional: `sell_prices.csv`) desde https://www.kaggle.com/competitions/m5-forecasting-accuracy/data . No incluimos una copia de los datos de terceros en GitHub.

Desde `mvp/` ejecuta:

```bash
python m5_import.py --sales /ruta/sales_train_validation.csv --calendar /ruta/calendar.csv --out .local/m5 --products 12 --days 365
python -m unittest discover -s tests -v
```

Esto crea `.local/m5/sales_m5_historico.csv` y `provenance.json`. **No crea inventario, vencimientos ni merma falsa**. Para probar el algoritmo de demanda, usa los datos históricos y el `backtest_sales` existente; el panel local de inventarios actuales no debe analizar el M5 antiguo como si fuera un negocio chileno en 2026.

El fichero `sales_m5_historico.csv` contiene observaciones históricas reales de ventas en unidades y ubicaciones del benchmark. Los precios son cero cuando no se proporciona `sell_prices.csv` y, si se proporcionan, corresponden al origen en **USD**, no a pesos chilenos. Las métricas monetarias del dashboard están expresadas en CLP, así que **no importes precios USD sin conversión documentada**. Se recomiendan pruebas de demanda basadas solo en cantidades.

### Qué falta para datos reales de merma

Conseguir consentimiento y convenio de piloto con uno o más comercios; solicitar lotes, vencimientos, ventas, stock y mermas observadas (sin datos personales innecesarios). No mezclar registros ficticios con históricos reales. Evaluar pronósticos fuera de muestra antes de hacer afirmaciones de reducción de mermas.

### Restricciones

- Procesamiento local, sin transmitir los datos a plataformas externas.
- Máximo 30 series y 365 días, limitando filas por las restricciones del MVP.
- Para ejecutar este módulo se utiliza solo la biblioteca estándar de Python 3.11+.
- `provenance.json` documenta la fuente y las advertencias de interpretación.
