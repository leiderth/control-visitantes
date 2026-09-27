# Módulo: GPS / Rastreo Satelital y Geocercas

## Modelo

`Vehiculo` (moto/carro/guardia a pie) — 1:1 — `DispositivoGPS` (el hardware/app
que reporta) — 1:N — `PosicionGPS` (cada punto de la traza, alta frecuencia).

`Geocerca` es circular (centro + radio en metros), no polígono — mantiene el
cálculo de entrada/salida en una distancia haversine simple, suficiente para
la mayoría de sedes.

## Endpoints (`/api/gps/`)

| Método | Ruta | Descripción |
|---|---|---|
| GET/POST | `vehiculos/` | Vehículos y guardias móviles |
| GET/POST | `dispositivos/` | Hardware/app GPS asociado a un vehículo |
| POST | `posiciones/` | Reporte de posición — al guardarse evalúa geocercas |
| GET | `geocerca-eventos/` | Historial de entradas/salidas (solo lectura) |
| GET/POST | `geocercas/` | Zonas autorizadas por sede |

## Cómo funciona la evaluación de geocercas

`apps/gps/services.py::evaluar_geocercas()` se ejecuta en cada `POST
/posiciones/`: compara la distancia del punto contra cada geocerca activa
del tenant y compara con el último `GeocercaEvento` de ese vehículo/geocerca
para no duplicar eventos mientras el vehículo permanece dentro o fuera.

## Pendiente para Fase 6

- Reemplazar el `POST /posiciones/` por un consumer de Channels (WebSocket)
  para que la traza no dependa de polling HTTP del dispositivo.
- Integrar una librería de mapas real (Mapbox o Google Maps) en
  `TrackingPage.tsx` — hoy muestra la lista de vehículos sin mapa, a la
  espera de la API key del cliente.
- Polígonos reales (no solo círculos) para sedes con perímetros irregulares.
