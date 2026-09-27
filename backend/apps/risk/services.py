from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import AccionCorrectiva, IncidenteRiesgo


@transaction.atomic
def transicionar_incidente(incidente_id, tenant_id, accion):
    incidente = get_object_or_404(
        IncidenteRiesgo.objects.select_for_update(), pk=incidente_id, tenant_id=tenant_id
    )
    transiciones = {
        "iniciar_seguimiento": (
            {IncidenteRiesgo.Estado.ABIERTO},
            IncidenteRiesgo.Estado.EN_SEGUIMIENTO,
        ),
        "resolver": (
            {IncidenteRiesgo.Estado.EN_SEGUIMIENTO},
            IncidenteRiesgo.Estado.RESUELTO,
        ),
        "cerrar": (
            {IncidenteRiesgo.Estado.RESUELTO},
            IncidenteRiesgo.Estado.CERRADO,
        ),
    }
    permitidos, nuevo_estado = transiciones[accion]
    if incidente.estado not in permitidos:
        raise ValidationError({"estado": f"No se puede {accion} un incidente en estado {incidente.estado}."})
    if accion == "cerrar" and incidente.acciones.exclude(
        estado=AccionCorrectiva.Estado.COMPLETADA
    ).exists():
        raise ValidationError(
            {"acciones": "Completa todas las acciones correctivas antes de cerrar el incidente."}
        )
    incidente.estado = nuevo_estado
    incidente.save(update_fields=["estado", "actualizado_en"])
    return incidente


@transaction.atomic
def transicionar_accion(accion_id, tenant_id, accion_solicitada):
    accion = get_object_or_404(
        AccionCorrectiva.objects.select_for_update().select_related("incidente"),
        pk=accion_id,
        tenant_id=tenant_id,
    )
    if accion.incidente.estado == IncidenteRiesgo.Estado.CERRADO:
        raise ValidationError({"incidente": "No se pueden modificar acciones de un incidente cerrado."})
    transiciones = {
        "iniciar": (
            {AccionCorrectiva.Estado.PENDIENTE},
            AccionCorrectiva.Estado.EN_PROGRESO,
        ),
        "completar": (
            {AccionCorrectiva.Estado.PENDIENTE, AccionCorrectiva.Estado.EN_PROGRESO},
            AccionCorrectiva.Estado.COMPLETADA,
        ),
    }
    permitidos, nuevo_estado = transiciones[accion_solicitada]
    if accion.estado not in permitidos:
        raise ValidationError({"estado": f"No se puede {accion_solicitada} una acción en estado {accion.estado}."})
    accion.estado = nuevo_estado
    campos = ["estado"]
    if accion_solicitada == "completar":
        accion.completada_en = timezone.now()
        campos.append("completada_en")
    accion.save(update_fields=campos)
    return accion
