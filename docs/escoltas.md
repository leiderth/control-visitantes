# Módulo: Escoltas

## Flujo de estados de un `ServicioEscolta`

```
programado → en_curso → finalizado
programado → cancelado
en_curso → cancelado
```

## Endpoints (`/api/escorts/`)

| Método | Ruta | Descripción |
|---|---|---|
| GET/POST | `servicios/` | Programación de servicios (cliente, ruta, vehículo, personal). El listado usa una versión liviana sin anidar checkpoints/alertas |
| GET | `servicios/{id}/` | Detalle completo, con `checkpoints_plan` y `alertas_panico` anidados |
| POST | `servicios/{id}/iniciar/` | Pasa a `en_curso` |
| POST | `servicios/{id}/finalizar/` | Pasa a `finalizado` |
| POST | `servicios/{id}/cancelar/` | Pasa a `cancelado` (acepta `motivo`) |
| POST | `servicios/{id}/panico/` | Botón de pánico — crea una `AlertaPanico` en estado `activa` |
| GET/POST | `checkpoints-plan/` | Puntos esperados de la ruta (orden, ubicación, hora estimada) |
| GET/POST | `checkpoints-registro/` | Confirmación real de paso; `a_tiempo` lo calcula el servidor, no el cliente |
| GET | `alertas-panico/` | Listado de alertas para la central |
| POST | `alertas-panico/{id}/atender/` | Asigna la alerta al operador que atiende |
| POST | `alertas-panico/{id}/cerrar/` | Cierra la alerta con notas de cierre |

## Validaciones del flujo

- Los estados solo avanzan por el flujo documentado: iniciar un servicio
  programado, finalizar uno en curso, o cancelar uno programado/en curso.
  Las transiciones no válidas responden `400`.
- Solo se dispara pánico durante un servicio en curso. Las alertas no se
  pueden crear directamente ni editar por CRUD: nacen desde el servicio y
  avanzan `activa → atendida → cerrada`.
- Las sedes, vehículos, checkpoints y personas asignadas deben pertenecer
  al tenant del usuario autenticado; el header `X-Tenant-Id` no permite
  cambiar de tenant. Super-admin conserva acceso entre tenants. Las
  consultas y transiciones también están limitadas al tenant.
- Un registro de checkpoint requiere un servicio en curso y coordenadas
  dentro de `radio_tolerancia_metros` del punto planeado. Latitud y longitud
  se validan en el servidor.
- El fin programado debe ser posterior al inicio. Los checkpoints se pueden
  editar o eliminar únicamente antes de iniciar el servicio. La ruta y la
  asignación del servicio quedan bloqueadas al iniciar; los servicios con
  actividad no se pueden eliminar.

## Decisiones de diseño

- `ServicioEscolta.vehiculo` reutiliza `apps.gps.Vehiculo` en vez de duplicar
  el catálogo — un mismo vehículo sirve tanto para rastreo GPS general como
  para un servicio de escolta puntual.
- `AlertaPanico` es un modelo propio del módulo, no un `AlarmEvent` de
  `apps.alarms`: nace de una acción del guardia en campo (botón/gesto), no
  de un sensor físico. El motor de correlación de riesgo (Fase 6+, sección
  5 del prompt de continuidad) es el que cruzará ambos si coinciden en
  tiempo/sede — ningún módulo depende del otro para funcionar solo.
- `CheckpointRegistro.a_tiempo` se calcula en `services.registrar_checkpoint`
  comparando `hora_estimada` del plan contra el momento del registro más una
  tolerancia fija (10 min) — deliberadamente no es un campo que envíe el
  cliente, para que el dato sea confiable en un reporte de cumplimiento.
- `radio_tolerancia_metros` se aplica con distancia Haversine en el servidor;
  la coordenada de un cliente móvil no basta para confirmar un checkpoint si
  no está físicamente cerca del punto planeado.
- Sin `hora_estimada` en el checkpoint, no hay nada contra qué comparar, así
  que el registro se marca `a_tiempo=True` por defecto.

## Pendiente (marcado como TODO en el código)

- Notificación inmediata a central al disparar el botón de pánico
  (WebSocket/push) — hoy depende del polling del panel, igual que
  `apps.alarms` mientras no exista el canal de Channels.
- App móvil de guardia offline-first: el botón de pánico y el registro de
  checkpoints deben poder dispararse sin señal y reintentar el POST al
  recuperar conexión.
- Alertas por checkpoint saltado (no solo tarde) y mapa de cobertura de la
  ruta quedan para el módulo de Rondas de guardia (guard tour), que
  comparte el mismo concepto de checkpoint pero para rondas fijas, no rutas
  de un solo trayecto.
