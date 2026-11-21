# MERMA360 IoT — gemelos digitales de equipos frigoríficos (prototipo)

## Objetivo
Conectar cámaras frigoríficas, vitrinas, congeladores y otros equipos que conservan perecibles, independientemente de marca cuando exista acceso técnico viable. **El módulo no está conectado a hardware real.**

## Arquitectura
Equipo moderno → controlador → pasarela industrial (Modbus TCP/RTU, OPC UA o API específica) → adaptador → lecturas normalizadas → gemelo digital → alertas → inventario/lotes.
Equipo antiguo → sensores externos independientes (temperatura, puerta, humedad, energía) → pasarela Wi-Fi/LTE/LoRaWAN según sitio → mismo flujo.
No se deben conectar sensores directamente a alimentación eléctrica o controles de compresor sin instalación autorizada.

## Prototipo incorporado
`digital_twin.py` define configuración por máquina, normalización de lecturas, control de orden temporal, estado y alertas configurables. Códigos: NO_DATA, STALE_TELEMETRY, FUTURE_TIMESTAMP, TEMP_OUT_OF_RANGE, HUMIDITY_LOW, HUMIDITY_HIGH, DOOR_OPEN, POWER_FAILURE. Ejecute `python mvp/iot/digital_twin.py` desde la raíz.

## Contrato de lectura JSON
```json
{"asset_id":"CF-001","observed_at":"2026-11-21T15:00:00Z","temp_c":4.1,"humidity_pct":76,"door_open":false,"power_ok":true}
```

## Pendiente antes de uso operativo
- Definir modelos concretos de controladores, fabricantes, acceso autorizado, protocolos y frecuencia de muestreo.
- Seleccionar sensores calibrables y mecanismos de seguridad, firma/autenticación del gateway, buffer offline, transmisión cifrada, almacenamiento histórico y reintentos.
- Vincular ubicación, activos y lotes reales en backend multiempresa con RLS, auditoría y permisos.
- Validar límites y tiempo de exposición por producto, criterio sanitario y normativa aplicable con profesional competente.
- Implementar notificaciones, escalamiento, mantenimiento y detección de anomalías basada en históricos reales.
- Probar con una cámara piloto y comparar alertas con registro de un termómetro de referencia.

Las alertas son de operación y no constituyen veredicto de inocuidad. No automatizar decisiones sanitarias, descartes ni activación de compresores.
