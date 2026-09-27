from django.db import transaction
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.permissions import (
    ADMIN_SUPERVISOR_ACCESS,
    READ_ACTIONS,
)
from apps.tenants.mixins import TenantScopedViewSetMixin

from .models import AlarmEvent, DespachoLog, Sensor
from .serializers import AlarmEventSerializer, AtenderAlarmaSerializer, SensorSerializer


class SensorViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Sensor.objects.select_related("sede").all()
    serializer_class = SensorSerializer
    role_permissions = ADMIN_SUPERVISOR_ACCESS


class AlarmEventViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """
    Panel central de monitoreo. El listado (GET /) es lo que alimenta la
    sala de monitoreo en tiempo real — en producción se complementa con un
    canal WebSocket que empuja estos mismos eventos (ver notas en el ViewSet).
    """

    queryset = AlarmEvent.objects.select_related("sensor", "sensor__sede").prefetch_related(
        "despachos"
    )
    serializer_class = AlarmEventSerializer
    filterset_fields = ["estado", "severidad", "sensor__sede"]
    ordering = ["-disparado_en"]
    role_permissions = {
        User.Rol.ADMIN_EMPRESA: ("list", "retrieve", "create", "update", "partial_update", "destroy", "atender", "cerrar", "marcar_falsa_alarma"),
        User.Rol.SUPERVISOR: ("list", "retrieve", "create", "update", "partial_update", "destroy", "atender", "cerrar", "marcar_falsa_alarma"),
        User.Rol.OPERADOR_CENTRAL: (*READ_ACTIONS, "atender", "cerrar", "marcar_falsa_alarma"),
    }

    # TODO (Fase 5): al crear un AlarmEvent (vía integración real del panel de
    # alarmas, no por este endpoint manual), publicar el evento en el grupo
    # WebSocket `alarmas:{tenant_id}` para actualizar la sala de monitoreo
    # sin polling.

    @action(detail=True, methods=["post"])
    def atender(self, request, pk=None):
        """Asigna el evento al operador que hace la petición (o al indicado en 'operador')."""
        evento = self.get_object()
        serializer = AtenderAlarmaSerializer(
            data=request.data,
            context={"request": request, "evento": evento},
        )
        serializer.is_valid(raise_exception=True)
        operador = serializer.validated_data.get("operador", request.user)
        if operador.tenant_id != evento.tenant_id or not operador.is_active:
            raise PermissionDenied("El operador debe estar activo y pertenecer a la empresa de la alarma.")
        with transaction.atomic():
            DespachoLog.objects.create(
                tenant=evento.tenant,
                evento=evento,
                operador=operador,
                comentario=serializer.validated_data.get("comentario", ""),
            )
            evento.estado = AlarmEvent.Estado.EN_ATENCION
            evento.atendido_en = evento.atendido_en or timezone.now()
            evento.save(update_fields=["estado", "atendido_en"])
        evento_actualizado = self.get_queryset().get(pk=evento.pk)
        return Response(self.get_serializer(evento_actualizado).data)

    @action(detail=True, methods=["post"])
    def cerrar(self, request, pk=None):
        evento = self.get_object()
        evento.estado = AlarmEvent.Estado.CERRADA
        evento.cerrado_en = timezone.now()
        evento.notas_cierre = request.data.get("notas_cierre", "")
        evento.save(update_fields=["estado", "cerrado_en", "notas_cierre"])
        return Response(self.get_serializer(evento).data)

    @action(detail=True, methods=["post"])
    def marcar_falsa_alarma(self, request, pk=None):
        evento = self.get_object()
        evento.estado = AlarmEvent.Estado.FALSA_ALARMA
        evento.cerrado_en = timezone.now()
        evento.save(update_fields=["estado", "cerrado_en"])
        return Response(self.get_serializer(evento).data)
