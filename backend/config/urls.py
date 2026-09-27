from django.contrib import admin
from django.urls import include, path

from .views import health_check

urlpatterns = [
    path("health/", health_check, name="health-check"),
    path("admin/", admin.site.urls),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/visitors/", include("apps.visitors.urls")),
    path("api/alarms/", include("apps.alarms.urls")),
    path("api/gps/", include("apps.gps.urls")),
    path("api/escorts/", include("apps.escorts.urls")),
    path("api/risk/", include("apps.risk.urls")),
]
