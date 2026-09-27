# Plataforma SaaS de Control de Visitantes y Gestión de Seguridad

Backend Django (modular, multi-tenant) + frontend React/Vite. Cada módulo
de negocio vive en `backend/apps/<módulo>/` y su contraparte de UI en
`frontend/src/features/<módulo>/`, siguiendo la misma convención en todas
las fases.

## Cómo correr el proyecto

Requisitos: Docker Desktop con Docker Compose y puertos locales `5173` y
`8000` disponibles.

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
docker compose up --build
```

- Backend: http://localhost:8000/api/
- Frontend: http://localhost:5173
- Admin: http://localhost:8000/admin/
- Salud del backend: http://localhost:8000/health/

Compose espera a que PostgreSQL acepte conexiones, ejecuta las migraciones
al iniciar el backend y conserva la base de datos y archivos subidos en
volúmenes. Los puertos de desarrollo se enlazan únicamente a `127.0.0.1`.
El archivo `.env` local no se versiona; `.env.example` es solo una plantilla:
define un secreto local propio y nunca reutilices esos valores en producción.
Este Compose ejecuta Django `runserver`/DEBUG y Vite en modo desarrollo; no
lo expongas a Internet. La configuración productiva exige una clave secreta
de al menos 50 caracteres y hosts explícitos mediante
`DJANGO_SETTINGS_MODULE=config.settings.prod`.

Al abrir el frontend, selecciona **Registrar empresa** para crear un tenant y
su primer administrador. El identificador elegido para la empresa se usa
después al iniciar sesión. El registro habilita los módulos ya implementados
(visitantes, alarmas, GPS, escoltas y riesgo); los usuarios adicionales y sus
roles se gestionan desde Django Admin.

## Arquitectura (resumen — ver docs/decisiones.md para el detalle completo)

- **Monolito modular** en Django: cada módulo es una app independiente,
  activable por tenant vía `apps.tenants.models.TenantModule` (feature flags).
- **Multi-tenancy**: `apps.tenants` — cada empresa de seguridad es un
  `Tenant`; `TenantScopedModel` y `TenantScopedViewSetMixin` (en
  `apps/tenants/mixins.py`) filtran datos en la capa de aplicación. Las
  políticas RLS de PostgreSQL siguen pendientes y aún no están activadas.
- **Roles**: `apps.accounts.User.Rol` — super-admin, admin de empresa,
  supervisor, operador de central, guardia, recepcionista, cliente final.

## Estado por fase

| Fase | Módulo | Contenido | Docs |
|---|---|---|---|
| 1 | Arquitectura | Modelo de datos, stack, roles (documento, no código) | — |
| 2 | Visitantes (núcleo) | Registro, check-in/check-out, watchlist | `docs/visitantes.md` |
| 3 | Visitantes (completo) | Invitaciones, firma electrónica, gafete QR, kiosco | `docs/visitantes.md` |
| 4 | Alarmas | Sensores, eventos, despacho (CAD), sala de monitoreo | `docs/alarmas.md` |
| 5 | GPS / Rastreo | Vehículos, posiciones, geocercas circulares con entrada/salida | `docs/gps-geocercas.md` |
| 6 | Escoltas | Programación de servicios, checkpoints de ruta, botón de pánico | `docs/escoltas.md` |
| 7 | Gestión de riesgo | Matriz de probabilidad/impacto, incidentes, acciones correctivas | `docs/riesgo.md` |
| 8 | Acceso y onboarding | Alta de empresa, inicio/renovación de sesión, controles de tenant | `docs/acceso.md` |
| 9+ | Rondas, CCTV, Control de acceso, facturación, informes y demás alcance | Pendiente | — |

### Módulo: Visitantes (`apps/visitors`)

Registro de visitantes, categorías (normal/contratista/proveedor/mensajería/
VIP/temporal), watchlist compartida entre sedes, flujo completo
`pendiente → autorizada → en_curso → finalizada`, pre-registro por
invitación (link/QR, confirmación pública sin login), firma electrónica
obligatoria por categoría antes del check-in, gafete con QR, y modo kiosco
para autoregistro en tablet de recepción.

**Pendiente (marcado como TODO en el código):** captura real de foto/firma
(hoy son placeholders visuales en el kiosco), envío real de invitación por
email/WhatsApp Business API, proveedor real de notificaciones push/SMS.

### Módulo: Alarmas (`apps/alarms`)

Sensores por sede (puerta, movimiento, pánico, incendio, perimetral),
eventos con severidad y flujo `activa → en_atencion → cerrada` (o
`falsa_alarma`), historial de despacho (`DespachoLog`) para el KPI de
tiempo de respuesta promedio, sala de monitoreo en tema oscuro.

**Pendiente:** canal WebSocket para reemplazar el polling actual,
integración real con paneles de alarma físicos (el campo
`Sensor.identificador_externo` ya deja el gancho).

### Módulo: GPS / Rastreo (`apps/gps`)

Vehículos (moto/carro/guardia a pie) con su dispositivo GPS asociado,
reporte de posiciones de alta frecuencia, y geocercas circulares por sede
que generan eventos de entrada/salida automáticamente (distancia
haversine, sin duplicar eventos mientras el vehículo permanece dentro).

**Pendiente:** mapa real (Mapbox/Google Maps, a la espera de la API key
del cliente — hoy `TrackingPage` muestra solo la lista de vehículos),
reporte de posición por WebSocket en vez de POST HTTP.

### Módulo: Escoltas (`apps/escorts`)

Programación de servicios de escolta (cliente, ruta, vehículo y personal
asignado — reutiliza `apps.gps.Vehiculo`), flujo
`programado → en_curso → finalizado` (o `cancelado`), checkpoints de
seguridad planeados por ruta con confirmación de paso por proximidad, y
botón de pánico por servicio con flujo de atención para la central. Las
relaciones y operaciones se aíslan por tenant asociado al usuario, y las
transiciones de estado inválidas se rechazan.

**Pendiente:** notificación inmediata a central (WebSocket) al disparar el
pánico, app móvil de guardia offline-first, alertas por checkpoint saltado
(quedan para el módulo de Rondas de guardia).

### Módulo: Gestión de riesgo (`apps/risk`)

Evaluaciones de vulnerabilidad por cliente/sede con puntaje calculado en
servidor (probabilidad × impacto, escala 1–5), nivel de riesgo derivado
(bajo/medio/alto/crítico), planes de mitigación y responsables. Incidentes
con severidad y flujo de seguimiento hasta cierre; el cierre exige completar
las acciones correctivas relacionadas. El frontend incluye matriz filtrable,
indicadores, registro de incidentes y gestión de acciones correctivas.

**Pendiente:** notificaciones y escalamiento automático de incidentes,
correlación de eventos entre módulos y exportación de informes de riesgo.

## Próximos módulos (Fase 8+)

Rondas de guardia (checkpoints NFC/QR/GPS para rondas fijas), CCTV (panel
centralizador de feeds) y Control de acceso físico (integración con
torniquetes/cerraduras).

## Alcance operativo pendiente

La plataforma ya ofrece un flujo local reproducible y los módulos indicados
en la tabla, pero aún no equivale a un despliegue SaaS de producción. No están
implementados todavía rondas, CCTV, control de acceso, facturación, dashboard
ejecutivo, exportación de reportes/evidencias, bitácora de cumplimiento,
motor de reglas/correlación, salud de dispositivos, ni app móvil offline.
También siguen pendientes las integraciones con proveedores externos,
notificaciones en tiempo real, políticas de RLS efectivas en PostgreSQL,
proxy TLS/servidor estático para despliegue, copias de seguridad y recuperación.
Consulta `docs/acceso.md` y los TODO de cada módulo antes de exponer el
sistema en Internet o procesar datos operativos reales.
