from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.permissions import (
    ADMIN_SUPERVISOR_ACCESS,
    READ_ACTIONS,
)
from apps.tenants.mixins import TenantScopedViewSetMixin

from .models import AccionCorrectiva, EvaluacionRiesgo, IncidenteRiesgo
from .permissions import IsTenantMember
from .serializers import (
    AccionCorrectivaSerializer,
    EvaluacionRiesgoSerializer,
    IncidenteRiesgoSerializer,
)
from .services import transicionar_accion, transicionar_incidente


class EvaluacionRiesgoViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = EvaluacionRiesgo.objects.select_related("sede", "responsable")
    serializer_class = EvaluacionRiesgoSerializer
    permission_classes = [IsTenantMember]
    filterset_fields = ["estado", "sede", "responsable"]
    search_fields = ["cliente_nombre", "vulnerabilidad"]
    role_permissions = ADMIN_SUPERVISOR_ACCESS

    def perform_destroy(self, instance):
        if instance.incidentes.exists():
            raise ValidationError(
                {"detail": "No se puede eliminar una evaluación vinculada a incidentes."}
            )
        instance.delete()


class IncidenteRiesgoViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = IncidenteRiesgo.objects.select_related(
        "sede", "evaluacion", "reportado_por"
    ).prefetch_related("acciones")
    serializer_class = IncidenteRiesgoSerializer
    permission_classes = [IsTenantMember]
    filterset_fields = ["estado", "severidad", "sede"]
    search_fields = ["cliente_nombre", "titulo", "descripcion"]
    ordering = ["-ocurrido_en"]
    role_permissions = {
        **{
            role: (
                "list", "retrieve", "create", "update", "partial_update", "destroy",
                "iniciar_seguimiento", "resolver", "cerrar",
            )
            for role in ADMIN_SUPERVISOR_ACCESS
        },
        User.Rol.OPERADOR_CENTRAL: (
            "list", "retrieve", "create", "iniciar_seguimiento", "resolver",
        ),
        User.Rol.GUARDIA: ("list", "retrieve", "create"),
    }

    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.tenant,
            reportado_por=self.request.user,
        )

    def perform_destroy(self, instance):
        if instance.estado != IncidenteRiesgo.Estado.ABIERTO:
            raise ValidationError(
                {"estado": "Solo se pueden eliminar incidentes que aún están abiertos."}
            )
        instance.delete()

    @action(detail=True, methods=["post"])
    def iniciar_seguimiento(self, request, pk=None):
        incidente = transicionar_incidente(pk, request.tenant.pk, "iniciar_seguimiento")
        return Response(self.get_serializer(incidente).data)

    @action(detail=True, methods=["post"])
    def resolver(self, request, pk=None):
        incidente = transicionar_incidente(pk, request.tenant.pk, "resolver")
        return Response(self.get_serializer(incidente).data)

    @action(detail=True, methods=["post"])
    def cerrar(self, request, pk=None):
        incidente = transicionar_incidente(pk, request.tenant.pk, "cerrar")
        return Response(self.get_serializer(incidente).data)


class AccionCorrectivaViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = AccionCorrectiva.objects.select_related("incidente", "responsable")
    serializer_class = AccionCorrectivaSerializer
    permission_classes = [IsTenantMember]
    filterset_fields = ["estado", "incidente", "responsable"]
    role_permissions = {
        **{
            role: (
                "list", "retrieve", "create", "update", "partial_update", "destroy",
                "iniciar", "completar",
            )
            for role in ADMIN_SUPERVISOR_ACCESS
        },
        User.Rol.OPERADOR_CENTRAL: READ_ACTIONS,
    }

    def perform_destroy(self, instance):
        if instance.estado == AccionCorrectiva.Estado.COMPLETADA:
            raise ValidationError({"estado": "No se puede eliminar una acción correctiva completada."})
        if instance.incidente.estado != IncidenteRiesgo.Estado.ABIERTO:
            raise ValidationError(
                {"incidente": "Solo se pueden eliminar acciones de incidentes abiertos."}
            )
        instance.delete()

    @action(detail=True, methods=["post"])
    def iniciar(self, request, pk=None):
        accion = transicionar_accion(pk, request.tenant.pk, "iniciar")
        return Response(self.get_serializer(accion).data)

    @action(detail=True, methods=["post"])
    def completar(self, request, pk=None):
        accion = transicionar_accion(pk, request.tenant.pk, "completar")
        return Response(self.get_serializer(accion).data)
