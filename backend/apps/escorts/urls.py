from rest_framework.routers import DefaultRouter

from .views import (
    AlertaPanicoViewSet,
    CheckpointPlanViewSet,
    CheckpointRegistroViewSet,
    ServicioEscoltaViewSet,
)

router = DefaultRouter()
router.register("servicios", ServicioEscoltaViewSet, basename="servicio-escolta")
router.register("checkpoints-plan", CheckpointPlanViewSet, basename="checkpoint-plan")
router.register("checkpoints-registro", CheckpointRegistroViewSet, basename="checkpoint-registro")
router.register("alertas-panico", AlertaPanicoViewSet, basename="alerta-panico")

urlpatterns = router.urls
