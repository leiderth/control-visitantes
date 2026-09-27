from rest_framework.routers import DefaultRouter

from .views import AlarmEventViewSet, SensorViewSet

router = DefaultRouter()
router.register("sensores", SensorViewSet, basename="sensor")
router.register("eventos", AlarmEventViewSet, basename="alarm-event")

urlpatterns = router.urls
