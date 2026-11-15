# Arquitectura evolutiva de Predice-IA

## Enfoque

La plataforma debe operar como capa de BI/decisiones conectada a Excel, CSV o un ERP existente, sin reemplazar las funciones de compras, stock, facturación o contabilidad del cliente.

## MVP local entregado

- Motor analítico reproducible, sin dependencias externas.
- Interfaz web para datos, escenarios y decisiones sugeridas.
- Datos persistentes **locales** en JSON con guardado atómico.
- Escenarios basados en supuestos públicos, nunca etiquetados como predicción probabilística calibrada.

## Próxima fase SaaS

1. **Autenticación y multiempresa:** usuarios, empresas, membresías, rol por empresa y MFA administrativa. Almacenar `organization_id` y políticas RLS en **cada** tabla de datos, además de pruebas automáticas de aislamiento; nunca confiar en un `organization_id` enviado por el navegador sin corroborar membresía.
2. **Persistencia confiable:** PostgreSQL con migraciones versionadas, transacciones para importaciones, claves únicas de archivos, respaldos, retención y recuperación verificada.
3. **Ingesta segura:** CSV/XLSX y conectores API con esquemas por cliente, detección de duplicados, vista previa, validación, idempotencia y conciliación de unidades.
4. **Motor de pronóstico validado:** modelo base (promedios), modelos estacionales, series intermitentes y pronósticos cuantílicos. Validar cada método con pruebas retrospectivas por SKU, local y período; conservar modelo base cuando el avanzado no mejora.
5. **Optimización con restricciones:** costos de compra, desperdicio, faltantes, capital, presupuesto, mínimos del proveedor y límites de vida útil. Registrar rango de incertidumbre y explicar cada sugerencia.
6. **Simulador de escenarios:** evaluar descuentos, redistribución o lotes especiales exclusivamente cuando son seguros y autorizados. Comparar alternativas bajo supuestos configurables y documentados.
7. **Evidencia de impacto:** registrar recomendaciones presentadas, aprobadas, rechazadas y ejecutadas; asociar resultados observados a un grupo de comparación/contrafactual prudente para evitar atribución de ahorro injustificada.
8. **Operación comercial:** API documentada, cuentas piloto, roles, auditoría, observabilidad, métricas de errores, SLA y facturación SaaS, sin convertirlo en ERP.

## Diseño lógico mínimo de datos

`organizations` → `memberships` → `imports` → `sales_daily` / `inventory_lots` / `waste_events` → `forecasts` → `recommendations` → `decisions` → `observed_outcomes`.

Todas las entidades empresariales deben estar asociadas a una organización de forma verificable. Asegurar permisos diferentes para lectura de análisis, administración de datos y aprobación de recomendaciones.

## Validación CORFO

Pilotos con varios negocios y seguimiento de indicadores: error de pronóstico (WAPE/MASE cuando corresponda), cobertura/calidad de datos, merma observada normalizada por ventas, quiebres de stock, margen y recuperación realmente ejecutada. Las mejoras deben contrastarse contra una línea base y analizar costos de adopción. La novedad debe probarse comparando alternativas existentes, no solo por incorporar la etiqueta “IA”.
