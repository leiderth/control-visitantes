# Módulo: Gestión de riesgo

El módulo mantiene evaluaciones de vulnerabilidad por cliente/sede, calcula
el nivel desde probabilidad e impacto y permite registrar incidentes con
acciones correctivas asignadas y seguimiento de estado.

## Matriz de riesgo

`EvaluacionRiesgo` tiene probabilidad e impacto en una escala de 1 a 5. El
puntaje se calcula en el servidor como `probabilidad × impacto` y el nivel se
deriva del puntaje:

| Puntaje | Nivel |
|---|---|
| 1–5 | Bajo |
| 6–11 | Medio |
| 12–19 | Alto |
| 20–25 | Crítico |

El nivel y el puntaje son de solo lectura en la API. Cada evaluación guarda
vulnerabilidad, contexto, plan de mitigación, estado de tratamiento,
responsable opcional y fecha de próxima revisión.

## Flujo de incidentes

```
abierto → en_seguimiento → resuelto → cerrado
```

Los incidentes guardan cliente, sede opcional, evaluación relacionada,
severidad, fecha de ocurrencia y usuario que reporta. El reporte queda
asociado al usuario autenticado y no puede suplantarse desde el payload.
Solo incidentes abiertos se pueden eliminar; incidentes cerrados no se
pueden editar.

## Acciones correctivas

Cada acción se asigna a un incidente y puede tener responsable, vencimiento y
descripción. Flujo:

```
pendiente → en_progreso → completada
pendiente → completada
```

Un incidente resuelto solo se puede cerrar cuando todas sus acciones
correctivas están completadas. No se permiten nuevas acciones en incidentes
resueltos o cerrados; las acciones completadas se conservan como historial.

## Endpoints (`/api/risk/`)

| Método | Ruta | Descripción |
|---|---|---|
| GET/POST | `evaluaciones/` | Listar y crear elementos de la matriz de riesgo |
| GET/PATCH/DELETE | `evaluaciones/{id}/` | Consultar y mantener una evaluación sin incidentes asociados |
| GET/POST | `incidentes/` | Listar y reportar incidentes |
| GET/PATCH/DELETE | `incidentes/{id}/` | Consultar/editar el incidente; solo se elimina mientras está abierto |
| POST | `incidentes/{id}/iniciar_seguimiento/` | Iniciar seguimiento |
| POST | `incidentes/{id}/resolver/` | Marcar como resuelto |
| POST | `incidentes/{id}/cerrar/` | Cerrar si no quedan acciones abiertas |
| GET/POST | `acciones/` | Consultar y crear acciones correctivas |
| POST | `acciones/{id}/iniciar/` | Pasar una acción pendiente a en progreso |
| POST | `acciones/{id}/completar/` | Completar una acción pendiente o en progreso |

## Aislamiento y validaciones

- Todos los modelos heredan `TenantScopedModel`; todos los ViewSets aplican
  `TenantScopedViewSetMixin` y requieren un usuario autenticado del tenant
  actual (super-admin conserva acceso entre tenants).
- Sede, evaluación, incidente y responsable relacionados se validan contra
  el tenant autenticado; también se valida que la sede de un incidente
  corresponda con la evaluación relacionada.
- El cierre y las transiciones de incidente/acción se ejecutan en
  transacciones con bloqueo de fila para evitar transiciones concurrentes
  contradictorias.

## Interfaz

`frontend/src/features/risk/` provee el panel responsive de matriz e
incidentes, filtros, formularios, seguimiento de acciones correctivas y
contadores operativos. El refresco es HTTP bajo demanda; no hay WebSocket
para riesgo todavía.
