"""
Piezas compartidas de aislamiento multi-tenant, usadas por TODOS los módulos
(visitors, alarms, gps, escorts, risk...). Se definieron aquí en la Fase 1
y cada módulo nuevo simplemente las reutiliza — es la pieza que hace que
"activar/desactivar módulo por tenant" y el aislamiento de datos funcionen
de forma consistente en todo el proyecto.
"""

from django.db import models


class TenantScopedModel(models.Model):
    """
    Base abstracta para cualquier modelo que pertenezca a un tenant.
    El aislamiento real ante fallos de código se refuerza con Row-Level
    Security (RLS) en PostgreSQL (ver docs/decisiones.md) — este campo es
    la mitad "capa de aplicación" de esa defensa en profundidad.
    """

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)

    class Meta:
        abstract = True


class TenantScopedViewSetMixin:
    """
    Filtra automáticamente el queryset por el tenant resuelto en el
    middleware (request.tenant, según subdominio o header) y lo inyecta
    al crear. Todos los ViewSets de todos los módulos heredan de esto en
    vez de repetir el filtro a mano.
    """

    site_scoped_lookups = {
        "visitors.Sede": "pk__in",
        "visitors.Host": "sede__in",
        "visitors.Visitor": "visitas__sede__in",
        "visitors.Visit": "sede__in",
        "visitors.Invitacion": "sede__in",
        "visitors.FirmaDocumento": "visita__sede__in",
        "alarms.Sensor": "sede__in",
        "alarms.AlarmEvent": "sensor__sede__in",
        "gps.Geocerca": "sede__in",
        "gps.GeocercaEvento": "geocerca__sede__in",
        "escorts.ServicioEscolta": "sede__in",
        "escorts.CheckpointPlan": "servicio__sede__in",
        "escorts.CheckpointRegistro": "checkpoint__servicio__sede__in",
        "escorts.AlertaPanico": "servicio__sede__in",
        "risk.EvaluacionRiesgo": "sede__in",
        "risk.IncidenteRiesgo": "sede__in",
        "risk.AccionCorrectiva": "incidente__sede__in",
    }

    def get_queryset(self):
        queryset = super().get_queryset().filter(tenant=self.request.tenant)
        user = self.request.user
        assigned_sites = getattr(user, "sedes", None)
        if not user.is_authenticated or assigned_sites is None or not assigned_sites.exists():
            return queryset

        lookup = self.site_scoped_lookups.get(
            f"{queryset.model._meta.app_label}.{queryset.model.__name__}"
        )
        if lookup is None:
            return queryset
        queryset = queryset.filter(**{lookup: assigned_sites.all()})
        if queryset.model.__name__ == "Visitor":
            queryset = queryset.distinct()
        return queryset

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)
