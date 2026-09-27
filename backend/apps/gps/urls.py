from rest_framework.routers import DefaultRouter

from .views import (
    DispositivoGPSViewSet,
    GeocercaEventoViewSet,
    GeocercaViewSet,
    PosicionGPSViewSet,
    VehiculoViewSet,
)

router = DefaultRouter()
router.register("vehiculos", VehiculoViewSet, basename="vehiculo")
router.register("dispositivos", DispositivoGPSViewSet, basename="dispositivo")
router.register("geocercas", GeocercaViewSet, basename="geocerca")
router.register("geocerca-eventos", GeocercaEventoViewSet, basename="geocerca-evento")
router.register("posiciones", PosicionGPSViewSet, basename="posicion")

urlpatterns = router.urls
