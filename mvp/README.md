# Predice-IA — Motor de decisiones preventivas (MVP técnico v0.3)

Sistema experimental de **predicción de mermas, compras inteligentes y simulación financiera**. No reemplaza el ERP: recibe lotes, ventas y eventos de merma mediante archivos CSV y los transforma en recomendaciones explicables. Conserva la terminología y el enfoque del prototipo MERMA360 IA; el **prototipo original del repositorio se conserva en `/index.html`** y no se modifica.

> **Estado:** implementación local funcional, con datos ficticios. No es una plataforma SaaS lista para producción: no incluye cuentas de usuarios, autorización multiempresa, backups remotos ni un modelo de aprendizaje automático entrenado. Sus recomendaciones requieren revisión humana.

## Ejecutar en Windows, macOS o Linux

Requiere **Python 3.11 o superior**. No utiliza dependencias externas.

```bash
python server.py
```

Abrir **http://127.0.0.1:8765/** en el mismo computador. Para detenerlo, `Ctrl+C`.

Para comprobar los cálculos y el servidor:

```bash
python -m unittest discover -s tests -v
```

Los datos ficticios se generan automáticamente la primera vez. Las cargas CSV quedan guardadas en `.local/datasets.json`, que no debe subirse a GitHub. Puedes restablecer la demostración desde el panel. El servidor escucha **solo `127.0.0.1`**; no debe publicarse ni exponerse mediante túneles hasta implementar autenticación y aislamiento de empresas.

## Lo que ya permite hacer

- **Lotes y riesgo:** estima unidades potencialmente no vendidas antes de su vencimiento, aplicando asignación FEFO para evitar duplicar la demanda entre lotes de un mismo SKU/local.
- **Mermas observadas:** separa los eventos registrados de la exposición futura estimada; no presenta la diferencia como ahorro logrado.
- **Demanda:** media ponderada entre días recientes e historial de 28 días, con dispersión y cobertura de datos. Usa tasa manual cuando no hay historial y reduce la confianza de la recomendación.
- **Compras inteligentes:** calcula horizonte = plazo de entrega + período de revisión; reserva de seguridad orientativa, stock utilizable y límite aproximado según vida útil.
- **Escenarios:** compara comprar cero, comprar la cantidad sugerida y una alternativa superior, mostrando ventas posibles, demanda no cubierta, excedente y contribución orientativa.
- **BI:** indicadores de valorización, exposición, merma registrada, lotes de riesgo, cobertura y priorización económica.
- **Integración:** carga CSV sin reemplazar el sistema de origen. Persiste los datos en el equipo local.

### Importación CSV

El archivo debe usar **UTF-8**, coma como separador, punto como separador decimal, fecha `AAAA-MM-DD` y los siguientes encabezados. Se aceptan columnas adicionales, que el motor conservará pero ignorará si no se utilizan.

**Lotes e inventario:**

```csv
code,sku,name,category,location,unit,quantity,unit_cost,unit_price,expires_on,manual_daily_sales,shelf_life_days
LOT-001,MANZ-RED,Manzana roja,Frutas y verduras,Local Temuco,kg,30,900,1800,2026-11-20,4,7
```

**Ventas diarias:**

```csv
sku,location,sold_on,quantity,unit_price
MANZ-RED,Local Temuco,2026-11-14,3,1800
```

**Mermas observadas:**

```csv
sku,location,occurred_on,quantity,unit_cost
MANZ-RED,Local Temuco,2026-11-14,2,900
```

Incluimos plantillas descargables en `data/`.

**Importante:** cada importación **reemplaza** todos los registros del tipo escogido, después de pedir confirmación. La interfaz no modifica ningún registro de un ERP, proveedor, marketplace ni Supabase. Cantidades y costos no pueden ser negativos. Límite: 20.000 registros por tipo, solicitud hasta 4 MB.

## Fórmulas iniciales (transparentes, no IA entrenada)

- `demanda_diaria = 0,65 × promedio último 7 días reportados + 0,35 × promedio 28 días reportados` cuando existen al menos tres días recientes; en caso contrario se usa el promedio histórico disponible. **Días sin registros no se interpretan como ventas cero.**
- `demanda_horizonte = demanda_diaria × (plazo_entrega + revisión)`.
- `stock_seguridad ≈ z × desviación_diaria × raíz(horizonte)` con `z` orientativo (90 %: 1,282; 95 %: 1,645; 98 %: 2,054). **No equivale a una probabilidad de servicio calibrada.**
- `compra_sugerida = máximo(0, techo(demanda_horizonte + stock_seguridad − stock_utilizable))`, acotada por una estimación de ventas antes del fin de la vida útil. Si la cobertura histórica es baja, se marca **revisión manual**.
- `exposición_lote = máximo(0, cantidad_lote − ventas_atribuibles_antes_de_vencer) × costo_unitario` con asignación FEFO.
- `contribución_aproximada = ventas_posibles × (precio − costo) − merma_proyectada × costo − penalización_teórica_por_inmovilización`; no incluye todos los costos ni sustituye la contabilidad.

### Limitaciones metodológicas

No hay modelo ML entrenado, evaluación *backtesting*, aprendizaje estacional calibrado, variables climáticas ni demanda probabilística validada. El nivel de confianza se basa **solo en cobertura de registros**, no en la precisión demostrada de predicción. Los escenarios emplean supuestos conservadores configurables. Un precio promocional, recuperación, transformación o donación debe validarse por inocuidad y normativas antes de ejecutarse. No cuantificar “ahorros logrados” sin una línea base y resultados observados.

## Estructura

```text
engine.py                 Cálculo de riesgo, demanda y escenarios
server.py                 API HTTP local, con validaciones y persistencia atómica
demo.py                   Datos de ejemplo ficticios
web/index.html            Dashboard responsivo
web/styles.css            Identidad visual Predice-IA
web/app.js                Presentación, CSV, configuración, simulación
data/                     Plantillas CSV
tests/                    Regresiones del motor y API
docs/                     Arquitectura y camino a SaaS
../index.html             Prototipo original del repositorio, conservado sin cambios
.github/workflows/        CI para pruebas automáticas
```

## Seguridad y condiciones para un SaaS comercial

El MVP **no** es multiempresa. Para producción será obligatorio: autenticación sólida, MFA administrativo, separación por `organization_id` en todas las tablas, políticas RLS verificadas, privacidad, registros de auditoría, control de importaciones, backups con restauración probada, HTTPS, monitoreo, límites de solicitudes, gestión de secretos, CI/CD y test de penetración. La propuesta en `docs/ARQUITECTURA.md` describe los siguientes pasos. No habilites acceso remoto al servidor incluido.

## Integración con GitHub

Este paquete se preparó a partir de un prototipo anterior de MERMA360 IA; **no procede de una clonación de `man-nuel-b/PREDICE-IA`**, porque la integración actual no puede leer el repositorio privado. **Antes de incorporarlo al repositorio original, comparar sus archivos y evitar sobrescribir funcionalidades existentes.**


## Actualización de interfaz: diseño oscuro adaptado (2026-11-15)

Se adaptó la propuesta visual proporcionada en \`predice_ia_interfaz_mejorada.zip\` al MVP funcional:
- Paleta oscura y acentos índigo, paneles más legibles, tabla y controles responsivos, estados de foco accesibles.
- Navegación interna activa y estado del motor conectado al servidor local.
- **No** se incorporó la fórmula de predicción simulada por X1/X2 ni una confianza ficticia de 98,4 %, porque reemplazaría los cálculos explicables de mermas y compras.
- Se conservan la importación CSV, recomendaciones por SKU/local, escenarios financieros y advertencias sobre límites del modelo.
- El diseño no constituye validación de precisión predictiva ni habilitación para desplegar el servidor sin autenticación.


## Analítica avanzada en el panel (2026-11-15)

La sección **Analítica avanzada** utiliza los lotes, ventas, eventos de merma y las salidas vigentes del motor, sin cambiar `engine.py`. Proporciona:
- Histórico semanal de **mermas observadas al costo** y ventas registradas a precio de venta, con filtros de 7, 28 y 56 días.
- Desglose por categoría de **exposición estimada actual**, distinto de las mermas observadas; análisis Pareto de SKU/local.
- Dispersión relativa de demanda (desviación / media), cobertura de datos, diagnóstico de registros insuficientes y filtros por local.
- Exportación CSV local con medidas identificadas y protección ante fórmulas de planilla.

**Advertencias:** El cambio de fecha afecta únicamente históricos; la exposición es una fotografía actual del inventario. Si hay ventas sin precio, el total comercial se muestra como parcial. La confianza indica cobertura de registros, **no exactitud del pronóstico**. No se calculan ahorros logrados ni probabilidades calibradas.

Pruebas: `node --test tests/advanced.test.cjs`; el CI las ejecuta junto con las pruebas Python existentes.
