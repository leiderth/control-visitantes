# Módulo: Monitoreo de Alarmas

## Flujo de estados de un `AlarmEvent`

```
activa → en_atencion → cerrada
activa → falsa_alarma
```

## Endpoints (`/api/alarms/`)

| Método | Ruta | Descripción |
|---|---|---|
| GET/POST | `sensores/` | Puntos monitoreados por sede (puerta, movimiento, pánico, incendio, perimetral) |
| GET/POST | `eventos/` | Disparos de sensores — el listado alimenta la sala de monitoreo |
| POST | `eventos/{id}/atender/` | Crea un `DespachoLog` y pasa a `en_atencion` |
| POST | `eventos/{id}/cerrar/` | Cierra el evento con notas de cierre |
| POST | `eventos/{id}/marcar_falsa_alarma/` | Cierra el evento como falsa alarma (para el KPI de alarmas atendidas vs. falsas) |

## Decisiones de diseño

- `DespachoLog` es un historial (no un campo único en `AlarmEvent`) para
  permitir reasignaciones sin perder el rastro de quién atendió qué y cuándo
  — importante para el reporte de "tiempo de respuesta promedio" del
  dashboard ejecutivo.
- `Sensor.identificador_externo` es el gancho para la integración real con
  paneles de alarma físicos (DSC, Honeywell, etc.); la integración en sí
  queda para el marketplace de conectores.

## Pendiente para Fase 5

- Canal WebSocket (`alarmas:{tenant_id}`) para reemplazar el polling del
  frontend por eventos push reales.
- Integración real con paneles de alarma vía su API/protocolo (el modelo ya
  deja el campo `identificador_externo` para mapear el evento externo).
- KPI de "tiempo de respuesta promedio" en el dashboard ejecutivo, calculado
  a partir de `disparado_en` → `atendido_en`.
