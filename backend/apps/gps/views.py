from rest_framework import viewsets

from apps.accounts.models import User
from apps.accounts.permissions import (
    ADMIN_SUPERVISOR_ACCESS,
    CENTRAL_OPERATIONS,
    READ_ACTIONS,
)
from apps.tenants.mixins import TenantScopedViewSetMixin

from .models import DispositivoGPS, Geocerca, GeocercaEvento, PosicionGPS, Vehiculo
from .serializers import (
    DispositivoGPSSerializer,
    GeocercaEventoSerializer,
    GeocercaSerializer,
    PosicionGPSSerializer,
    VehiculoSerializer,
)
from .services import evaluar_geocercas


class VehiculoViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Vehiculo.objects.select_related("asignado_a").all()
    serializer_class = VehiculoSerializer
    role_permissions = ADMIN_SUPERVISOR_ACCESS


class DispositivoGPSViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = DispositivoGPS.objects.select_related("vehiculo").all()
    serializer_class = DispositivoGPSSerializer
    role_permissions = ADMIN_SUPERVISOR_ACCESS


class GeocercaViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Geocerca.objects.all()
    serializer_class = GeocercaSerializer
    role_permissions = ADMIN_SUPERVISOR_ACCESS


class GeocercaEventoViewSet(TenantScopedViewSetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = GeocercaEvento.objects.select_related("geocerca", "vehiculo").all()
    serializer_class = GeocercaEventoSerializer
    filterset_fields = ["vehiculo", "geocerca", "tipo"]
    role_permissions = {
        **{role: READ_ACTIONS for role in (*CENTRAL_OPERATIONS, User.Rol.GUARDIA)},
    }


class PosicionGPSViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """
    Solo creación real desde el dispositivo/app del guardia (alta frecuencia).
    Al guardar, evalúa geocercas — igual que hoy vía HTTP; en Fase 6 este
    create() se reemplaza por un consumer de Channels que recibe el mismo
    payload por WebSocket sin cambiar `services.evaluar_geocercas`.
    """

    queryset = PosicionGPS.objects.select_related("dispositivo").all()
    serializer_class = PosicionGPSSerializer
    http_method_names = ["get", "post"]
    role_permissions = {
        **{role: READ_ACTIONS for role in CENTRAL_OPERATIONS},
        User.Rol.GUARDIA: ("list", "retrieve", "create"),
    }

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.rol == User.Rol.GUARDIA:
            queryset = queryset.filter(dispositivo__vehiculo__asignado_a=self.request.user)
        return queryset

    def perform_create(self, serializer):
        posicion = serializer.save(tenant=self.request.tenant)
        evaluar_geocercas(posicion)
