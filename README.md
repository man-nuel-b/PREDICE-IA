# MERMA360 IA — nuevo proyecto

**Objetivo:** plataforma SaaS multiempresa para prevenir, medir y revalorizar mermas en alimentos, retail, agroindustria y ferias libres.

## Entrega inicial (08-11-2026)
- `index.html`: prototipo navegable sin instalación que funciona localmente en el navegador.
- Panel de KPIs, clasificación de riesgo por lotes, inventario editable, alertas, escenarios de recuperación, historial de acciones y exportación CSV.
- Datos de ejemplo ficticios, marcados explícitamente como demostración.
- Persistencia en `localStorage` del navegador; no hay backend ni sincronización entre dispositivos.

## Uso
1. Descarga `index.html` y ábrelo con Chrome o Edge.
2. Revisa el panel y entra en Inventario para registrar un lote.
3. En Recuperación escoge el lote y compara posibles estrategias.
4. Si ejecutas una acción real, registra el monto neto efectivamente recuperado.
5. Exporta CSV para respaldar los lotes de prueba.

## Límites actuales
- El índice de riesgo usa reglas transparentes basadas en días, inventario y rotación; **no es todavía IA entrenada**.
- Los escenarios de recuperación son simulaciones, no recomendaciones sanitarias ni comerciales garantizadas.
- No hay autenticación, autorización, integración con POS/ERP, conexión a WhatsApp, API ni base de datos remota.
- No usar para decisiones operativas de inocuidad alimentaria ni para registrar datos sensibles reales.

## Ruta de desarrollo
1. Entrevistas, definición de unidad y lote y criterios de inocuidad.
2. Backend y esquema multi-tenant aislado, roles, auditoría y autenticación.
3. Integraciones de CSV/ERP/POS y control de calidad de datos.
4. Histórico suficiente para construir y evaluar modelos predictivos por categoría.
5. Motor de acciones con cálculo de margen real, aprobación humana y trazabilidad.
6. Pilotos en tres negocios de La Araucanía con medición antes/después.

**Nota de continuidad:** este archivo conserva una síntesis del proyecto, pero no es una copia literal de toda la conversación de ChatGPT.

## Nueva versión: motor de decisiones preventivas (15-11-2026)

El desarrollo evoluciona en la carpeta **[`mvp/`](mvp/README.md)** con el prototipo antiguo conservado en [`legacy/index.html`](legacy/index.html). La portada pública `index.html` muestra ahora la interfaz mejorada de demostración.

Esta versión incluye pronóstico orientativo de demanda, cálculo de exposición a mermas por lote, compras recomendadas según vida útil, simulador financiero, BI, importación CSV, servidor local Python y pruebas automáticas.

**Ejecutar desde el repositorio clonado:**

```bash
cd mvp
python server.py
```

Abre `http://127.0.0.1:8765/`. Para las pruebas: `python -m unittest discover -s tests -v` dentro de `mvp/`.

> **No publicar `mvp/server.py` en Internet:** no tiene autenticación ni separación multiempresa. Sus cálculos son heurísticos, todavía no un modelo de IA entrenado y calibrado. Los datos de demostración son ficticios.


## Demostración pública

La página de GitHub Pages sirve la interfaz oscura de Predice-IA con Analítica Avanzada y datos ficticios desde la raíz. `index.html` y `demo/index.html` son deliberadamente idénticos para que la publicación funcione tanto desde la rama `main` como con el workflow `pages-demo.yml`. El prototipo MERMA360 anterior está archivado en `legacy/index.html`. La versión web pública no ejecuta el servidor Python, ni importa CSV ni guarda datos de usuario.
