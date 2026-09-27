"""
Servicios de negocio del módulo de Visitantes que no encajan como método
de modelo: notificaciones al anfitrión y generación del gafete.

Se aíslan aquí (en vez de dejarlos en views.py) porque en la Fase 4 pasan
a ejecutarse como tareas asíncronas (Celery) sin tocar la capa HTTP.
"""

import io

import qrcode
from django.core.files.base import ContentFile

from .models import Host, Visit


def notificar_anfitrion(visita: Visit, evento: str) -> None:
    """
    Envía una notificación al anfitrión por los canales activos en
    Host.notificar_por (push/sms/email).

    TODO (Fase 4): integrar con proveedor real (FCM para push, Twilio o
    WhatsApp Business API para sms/whatsapp, backend de email del proyecto).
    Por ahora solo registra la intención — útil para pruebas y para no
    bloquear el flujo de check-in mientras se conecta el proveedor real.
    """
    host: Host | None = visita.anfitrion
    if host is None:
        return

    canales = host.notificar_por or []
    for canal in canales:
        # cada rama sería una llamada real distinta (fcm.send, twilio.send, email.send)
        print(f"[notificación:{canal}] a {host.email} — visita #{visita.id}: {evento}")


def generar_gafete_qr(visita: Visit) -> ContentFile:
    """
    Genera la imagen QR del gafete a partir de codigo_qr de la visita.
    El QR codifica solo el UUID de la visita; el kiosco/lector valida
    contra el backend (nunca se embebe información sensible en el propio QR).
    """
    img = qrcode.make(str(visita.codigo_qr))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"gafete-{visita.id}.png")
