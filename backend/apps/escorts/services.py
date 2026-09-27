"""
Lógica que no es puramente HTTP, siguiendo la misma separación que
apps.gps.services y apps.visitors.services: aislada de las vistas para que
en Fase 6+ (reporte de checkpoint por WebSocket/app móvil offline-first en
vez de POST HTTP directo) se reutilice sin tocar este cálculo.
"""

from datetime import timedelta
import math

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import AlertaPanico, CheckpointPlan, CheckpointRegistro, ServicioEscolta

TOLERANCIA_MINUTOS_DEFECTO = 10


def _distancia_metros(lat1, lng1, lat2, lng2):
    radio_tierra = 6_371_000
    lat1, lat2 = math.radians(float(lat1)), math.radians(float(lat2))
    delta_lat = lat2 - lat1
    delta_lng = math.radians(float(lng2) - float(lng1))
    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lng / 2) ** 2
    )
    return radio_tierra * 2 * math.atan2(math.sqrt(haversine), math.sqrt(1 - haversine))


@transaction.atomic
def transicionar_servicio(servicio_id, tenant_id, accion, motivo=""):
    servicio = get_object_or_404(
        ServicioEscolta.objects.select_for_update(), pk=servicio_id, tenant_id=tenant_id
    )
    transiciones = {
        "iniciar": ({ServicioEscolta.Estado.PROGRAMADO}, ServicioEscolta.Estado.EN_CURSO),
        "finalizar": ({ServicioEscolta.Estado.EN_CURSO}, ServicioEscolta.Estado.FINALIZADO),
        "cancelar": (
            {ServicioEscolta.Estado.PROGRAMADO, ServicioEscolta.Estado.EN_CURSO},
            ServicioEscolta.Estado.CANCELADO,
        ),
    }
    estados_permitidos, nuevo_estado = transiciones[accion]
    if servicio.estado not in estados_permitidos:
        raise ValidationError({"estado": f"No se puede {accion} un servicio en estado {servicio.estado}."})

    campos_actualizados = ["estado"]
    servicio.estado = nuevo_estado
    if accion == "iniciar":
        servicio.iniciado_en = timezone.now()
        campos_actualizados.append("iniciado_en")
    elif accion == "finalizar":
        servicio.finalizado_en = timezone.now()
        campos_actualizados.append("finalizado_en")
    elif motivo:
        servicio.notas = motivo
        campos_actualizados.append("notas")
    servicio.save(update_fields=campos_actualizados)
    return servicio


@transaction.atomic
def disparar_panico(servicio_id, tenant_id, usuario, lat=None, lng=None):
    servicio = get_object_or_404(
        ServicioEscolta.objects.select_for_update(), pk=servicio_id, tenant_id=tenant_id
    )
    if servicio.estado != ServicioEscolta.Estado.EN_CURSO:
        raise ValidationError({"estado": "Solo se puede activar pánico en un servicio en curso."})
    return AlertaPanico.objects.create(
        tenant_id=tenant_id,
        servicio=servicio,
        lat=lat,
        lng=lng,
        disparado_por=usuario,
    )


@transaction.atomic
def atender_alerta_panico(alerta_id, tenant_id, usuario):
    alerta = get_object_or_404(
        AlertaPanico.objects.select_for_update(), pk=alerta_id, tenant_id=tenant_id
    )
    if alerta.estado != AlertaPanico.Estado.ACTIVA:
        raise ValidationError({"estado": "Solo se pueden atender alertas de pánico activas."})
    alerta.estado = AlertaPanico.Estado.ATENDIDA
    alerta.atendido_en = timezone.now()
    alerta.atendido_por = usuario
    alerta.save(update_fields=["estado", "atendido_en", "atendido_por"])
    return alerta


@transaction.atomic
def cerrar_alerta_panico(alerta_id, tenant_id, notas_cierre=""):
    alerta = get_object_or_404(
        AlertaPanico.objects.select_for_update(), pk=alerta_id, tenant_id=tenant_id
    )
    if alerta.estado != AlertaPanico.Estado.ATENDIDA:
        raise ValidationError({"estado": "La alerta debe estar atendida antes de cerrarse."})
    alerta.estado = AlertaPanico.Estado.CERRADA
    alerta.cerrado_en = timezone.now()
    alerta.notas_cierre = notas_cierre
    alerta.save(update_fields=["estado", "cerrado_en", "notas_cierre"])
    return alerta


def registrar_checkpoint(
    checkpoint: CheckpointPlan, lat, lng, usuario=None, momento=None
) -> CheckpointRegistro:
    """
    Crea el registro de paso y calcula `a_tiempo` contra `hora_estimada`
    del plan (si existe) más una tolerancia fija. Sin `hora_estimada`
    definida no hay nada contra qué comparar, así que se marca a_tiempo=True
    por defecto (no hay retraso que detectar).
    """
    if checkpoint.tenant_id != checkpoint.servicio.tenant_id:
        raise ValidationError({"checkpoint": "El checkpoint y el servicio deben pertenecer al mismo tenant."})
    if checkpoint.servicio.estado != ServicioEscolta.Estado.EN_CURSO:
        raise ValidationError({"checkpoint": "El servicio debe estar en curso para registrar un paso."})
    distancia = _distancia_metros(lat, lng, checkpoint.lat, checkpoint.lng)
    if distancia > checkpoint.radio_tolerancia_metros:
        raise ValidationError(
            {"detail": "La ubicación reportada está fuera del radio permitido para este checkpoint."}
        )

    momento = momento or timezone.now()
    a_tiempo = True
    if checkpoint.hora_estimada:
        limite = checkpoint.hora_estimada + timedelta(minutes=TOLERANCIA_MINUTOS_DEFECTO)
        a_tiempo = momento <= limite

    return CheckpointRegistro.objects.create(
        tenant=checkpoint.tenant,
        checkpoint=checkpoint,
        lat=lat,
        lng=lng,
        reportado_por=usuario,
        a_tiempo=a_tiempo,
    )
