from rest_framework.routers import DefaultRouter

from .views import (
    DocumentoLegalViewSet,
    FirmaDocumentoViewSet,
    HostViewSet,
    InvitacionPublicaViewSet,
    InvitacionViewSet,
    SedeViewSet,
    VisitorViewSet,
    VisitViewSet,
    WatchlistEntryViewSet,
)

router = DefaultRouter()
router.register("sedes", SedeViewSet, basename="sede")
router.register("hosts", HostViewSet, basename="host")
router.register("visitantes", VisitorViewSet, basename="visitor")
router.register("watchlist", WatchlistEntryViewSet, basename="watchlist")
router.register("visitas", VisitViewSet, basename="visit")
router.register("documentos-legales", DocumentoLegalViewSet, basename="documento-legal")
router.register("firmas", FirmaDocumentoViewSet, basename="firma")
router.register("invitaciones", InvitacionViewSet, basename="invitacion")
# Rutas públicas (sin login) para confirmación de pre-registro por link/QR:
router.register("invitaciones-publicas", InvitacionPublicaViewSet, basename="invitacion-publica")

urlpatterns = router.urls
