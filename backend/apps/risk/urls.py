from rest_framework.routers import DefaultRouter

from .views import AccionCorrectivaViewSet, EvaluacionRiesgoViewSet, IncidenteRiesgoViewSet

router = DefaultRouter()
router.register("evaluaciones", EvaluacionRiesgoViewSet, basename="evaluacion-riesgo")
router.register("incidentes", IncidenteRiesgoViewSet, basename="incidente-riesgo")
router.register("acciones", AccionCorrectivaViewSet, basename="accion-correctiva")

urlpatterns = router.urls
