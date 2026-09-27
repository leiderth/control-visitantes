# Módulo: Control de Visitantes

## Flujo de estados de una `Visit`

```
pendiente → autorizada → en_curso → finalizada
                              ↘ excedida (si pasa hora_autorizada_hasta sin check-out)
pendiente → rechazada
```

## Endpoints (`/api/visitors/`)

| Método | Ruta | Descripción |
|---|---|---|
| GET/POST | `sedes/` | Sedes del tenant |
| GET/POST | `hosts/` | Anfitriones por sede |
| GET/POST | `visitantes/` | Personas (globales al tenant, no por sede) |
| GET/POST | `watchlist/` | Lista negra / vigilancia, compartida entre sedes |
| GET/POST | `visitas/` | Registros de ingreso |
| POST | `visitas/{id}/autorizar/` | Pasa de `pendiente` a `autorizada` |
| POST | `visitas/{id}/check_in/` | Registra hora de ingreso, pasa a `en_curso` |
| POST | `visitas/{id}/check_out/` | Registra hora de salida, pasa a `finalizada` |

## Pendiente para Fase 3 (mockups) y Fase 4 (avanzado)

- Job periódico (Celery) que marca visitas `en_curso` como `excedida` cuando se pasa `hora_autorizada_hasta`.
- Notificación al anfitrión (push/SMS/email) en el `check_in`, según `Host.notificar_por`.
- Generación real de PDF/QR para el gafete imprimible.
- Firma electrónica de documentos (NDA, políticas) antes de habilitar el check-in.
- Endpoint de pre-registro público (sin login) para invitaciones por link/QR.

## Fase 3 — completado en esta entrega

- **Pre-registro/invitaciones**: `Invitacion` con `token` único; endpoint público
  `invitaciones-publicas/{token}/confirmar/` (sin login) para que el visitante
  confirme desde el link/QR recibido.
- **Firma electrónica**: `DocumentoLegal` (plantillas) + `FirmaDocumento` (firma
  concreta por visita). El `check_in` ahora **bloquea** si faltan firmas
  obligatorias para la categoría del visitante (ver `obligatorio_para`).
- **Gafete QR**: `visitas/{id}/gafete/` genera y persiste la imagen QR (codifica
  solo el UUID de la visita, nunca datos sensibles).
- **Notificación al anfitrión**: `services.notificar_anfitrion()` se invoca en
  el check-in — implementación real de push/SMS/WhatsApp queda para Fase 4.
- **Modo kiosco**: `KioskPage.tsx`, flujo lineal de un paso por pantalla para
  que el visitante se autoregistre sin asistencia.

## Pendiente real para Fase 4

- Captura de foto real (getUserMedia) en el kiosco — hoy es un placeholder.
- Envío real de la invitación (email/WhatsApp Business API) con el link/QR.
- Integración de proveedor real de notificaciones (FCM, Twilio).
- Job Celery que marca visitas como `excedida` al pasar `hora_autorizada_hasta`.
