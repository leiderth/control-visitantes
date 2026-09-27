from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.permissions import (
    ADMIN_SUPERVISOR_ACCESS,
    CENTRAL_OPERATIONS,
    READ_ACTIONS,
)
from apps.tenants.mixins import TenantScopedViewSetMixin

from .models import AlertaPanico, CheckpointPlan, CheckpointRegistro, ServicioEscolta
from .permissions import IsTenantMember
from .serializers import (
    AlertaPanicoSerializer,
    CancelarServicioSerializer,
    CheckpointPlanSerializer,
    CheckpointRegistroSerializer,
    CierreAlertaPanicoSerializer,
    CoordenadasSerializer,
    ServicioEscoltaListSerializer,
    ServicioEscoltaSerializer,
)
from .services import (
    atender_alerta_panico,
    cerrar_alerta_panico,
    disparar_panico,
    registrar_checkpoint,
    transicionar_servicio,
)


class ServicioEscoltaViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = ServicioEscolta.objects.select_related("sede", "vehiculo").prefetch_related(
        "personal", "checkpoints_plan", "alertas_panico"
    )
    permission_classes = [IsTenantMember]
    filterset_fields = ["estado", "sede", "vehiculo"]
    ordering = ["-programado_inicio"]
    role_permissions = {
        **{
            role: (
                "list", "retrieve", "create", "update", "partial_update", "destroy",
                "iniciar", "finalizar", "cancelar", "panico",
            )
            for role in CENTRAL_OPERATIONS
        },
        User.Rol.GUARDIA: ("list", "retrieve", "iniciar", "finalizar", "panico"),
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.rol == User.Rol.GUARDIA:
            queryset = queryset.filter(personal=self.request.user)
        return queryset

    def get_serializer_class(self):
        if self.action == "list":
            return ServicioEscoltaListSerializer
        return ServicioEscoltaSerializer

    def perform_destroy(self, instance):
        if instance.estado != ServicioEscolta.Estado.PROGRAMADO:
            raise ValidationError({"estado": "No se puede eliminar un servicio que ya inició."})
        instance.delete()

    @action(detail=True, methods=["post"])
    def iniciar(self, request, pk=None):
        servicio = transicionar_servicio(pk, request.tenant.pk, "iniciar")
        return Response(ServicioEscoltaSerializer(servicio).data)

    @action(detail=True, methods=["post"])
    def finalizar(self, request, pk=None):
        servicio = transicionar_servicio(pk, request.tenant.pk, "finalizar")
        return Response(ServicioEscoltaSerializer(servicio).data)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        datos = CancelarServicioSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        servicio = transicionar_servicio(
            pk, request.tenant.pk, "cancelar", motivo=datos.validated_data.get("motivo", "")
        )
        return Response(ServicioEscoltaSerializer(servicio).data)

    @action(detail=True, methods=["post"])
    def panico(self, request, pk=None):
        """
        Botón de pánico: lo dispara el guardia desde la app móvil (Fase 6+;
        hoy el endpoint HTTP es el gancho). Crea la alerta y queda a la
        vista de `AlertaPanicoViewSet` para la central.

        TODO (Fase 6+): notificación inmediata a central (WebSocket/push) en
        vez de depender del polling del panel de monitoreo.
        """
        datos = CoordenadasSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        alerta = disparar_panico(
            pk,
            request.tenant.pk,
            request.user if request.user.is_authenticated else None,
            lat=datos.validated_data.get("lat"),
            lng=datos.validated_data.get("lng"),
        )
        return Response(AlertaPanicoSerializer(alerta).data, status=201)


class CheckpointPlanViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = CheckpointPlan.objects.select_related("servicio").prefetch_related("registros")
    serializer_class = CheckpointPlanSerializer
    permission_classes = [IsTenantMember]
    filterset_fields = ["servicio"]
    role_permissions = {
        **{role: ("list", "retrieve", "create", "update", "partial_update", "destroy") for role in ADMIN_SUPERVISOR_ACCESS},
        User.Rol.GUARDIA: READ_ACTIONS,
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.rol == User.Rol.GUARDIA:
            queryset = queryset.filter(servicio__personal=self.request.user)
        return queryset

    def perform_destroy(self, instance):
        if instance.servicio.estado != ServicioEscolta.Estado.PROGRAMADO:
            raise ValidationError(
                {"servicio": "No se pueden eliminar checkpoints después de iniciar el servicio."}
            )
        instance.delete()


class CheckpointRegistroViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """
    Solo lectura + creación: un registro de paso no se edita, se corrige
    creando uno nuevo (igual criterio que `apps.gps.PosicionGPS`).
    """

    queryset = CheckpointRegistro.objects.select_related("checkpoint").all()
    serializer_class = CheckpointRegistroSerializer
    permission_classes = [IsTenantMember]
    filterset_fields = ["checkpoint"]
    http_method_names = ["get", "post"]
    role_permissions = {
        **{role: ("list", "retrieve", "create") for role in CENTRAL_OPERATIONS},
        User.Rol.GUARDIA: ("list", "retrieve", "create"),
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.rol == User.Rol.GUARDIA:
            queryset = queryset.filter(checkpoint__servicio__personal=self.request.user)
        return queryset

    def perform_create(self, serializer):
        # No se usa serializer.save(): `a_tiempo` no lo decide el cliente que
        # reporta, lo calcula `services.registrar_checkpoint` — se le asigna
        # el resultado a `serializer.instance` para que la respuesta HTTP
        # (serializer.data) refleje el registro real ya creado.
        checkpoint = serializer.validated_data["checkpoint"]
        serializer.instance = registrar_checkpoint(
            checkpoint=checkpoint,
            lat=serializer.validated_data["lat"],
            lng=serializer.validated_data["lng"],
            usuario=self.request.user if self.request.user.is_authenticated else None,
        )


class AlertaPanicoViewSet(TenantScopedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = AlertaPanico.objects.select_related("servicio").all()
    serializer_class = AlertaPanicoSerializer
    permission_classes = [IsTenantMember]
    filterset_fields = ["estado", "servicio"]
    role_permissions = {
        **{role: (*READ_ACTIONS, "atender", "cerrar") for role in CENTRAL_OPERATIONS},
        User.Rol.GUARDIA: READ_ACTIONS,
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.rol == User.Rol.GUARDIA:
            queryset = queryset.filter(servicio__personal=self.request.user)
        return queryset

    @action(detail=True, methods=["post"])
    def atender(self, request, pk=None):
        alerta = atender_alerta_panico(
            pk, request.tenant.pk, request.user if request.user.is_authenticated else None
        )
        return Response(self.get_serializer(alerta).data)

    @action(detail=True, methods=["post"])
    def cerrar(self, request, pk=None):
        datos = CierreAlertaPanicoSerializer(data=request.data)
        datos.is_valid(raise_exception=True)
        alerta = cerrar_alerta_panico(
            pk, request.tenant.pk, notas_cierre=datos.validated_data.get("notas_cierre", "")
        )
        return Response(self.get_serializer(alerta).data)
