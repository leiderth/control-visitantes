from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import User
from apps.accounts.permissions import (
    ADMIN_SUPERVISOR_ACCESS,
    READ_ACTIONS,
    SITE_READ_ACCESS,
)
from apps.tenants.mixins import TenantScopedViewSetMixin

from .models import (
    DocumentoLegal,
    FirmaDocumento,
    Host,
    Invitacion,
    Sede,
    Visit,
    Visitor,
    WatchlistEntry,
)
from .serializers import (
    DocumentoLegalSerializer,
    FirmaDocumentoSerializer,
    HostSerializer,
    InvitacionPublicaSerializer,
    InvitacionSerializer,
    SedeSerializer,
    VisitorSerializer,
    VisitSerializer,
    WatchlistEntrySerializer,
)
from .services import generar_gafete_qr, notificar_anfitrion


class SedeViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Sede.objects.all()
    serializer_class = SedeSerializer
    role_permissions = {
        **ADMIN_SUPERVISOR_ACCESS,
        **SITE_READ_ACCESS,
    }


class HostViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Host.objects.select_related("sede").all()
    serializer_class = HostSerializer
    role_permissions = {
        **ADMIN_SUPERVISOR_ACCESS,
        User.Rol.RECEPCIONISTA: READ_ACTIONS,
    }


class VisitorViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    filterset_fields = ["categoria"]
    search_fields = ["documento_numero", "nombre_completo", "empresa"]
    role_permissions = {
        User.Rol.ADMIN_EMPRESA: ("list", "retrieve", "create", "update", "partial_update", "destroy"),
        User.Rol.SUPERVISOR: ("list", "retrieve", "create", "update", "partial_update", "destroy"),
        User.Rol.RECEPCIONISTA: ("list", "retrieve", "create", "update", "partial_update"),
        User.Rol.GUARDIA: READ_ACTIONS,
        User.Rol.OPERADOR_CENTRAL: READ_ACTIONS,
    }


class WatchlistEntryViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = WatchlistEntry.objects.all()
    serializer_class = WatchlistEntrySerializer
    role_permissions = ADMIN_SUPERVISOR_ACCESS

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant, registrado_por=self.request.user)


class DocumentoLegalViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = DocumentoLegal.objects.filter(activo=True)
    serializer_class = DocumentoLegalSerializer
    role_permissions = ADMIN_SUPERVISOR_ACCESS


class FirmaDocumentoViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    queryset = FirmaDocumento.objects.all()
    serializer_class = FirmaDocumentoSerializer
    role_permissions = {
        User.Rol.ADMIN_EMPRESA: ("list", "retrieve", "create", "update", "partial_update", "destroy"),
        User.Rol.SUPERVISOR: ("list", "retrieve", "create", "update", "partial_update", "destroy"),
        User.Rol.RECEPCIONISTA: ("list", "retrieve", "create"),
    }

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant, ip_origen=self.request.META.get("REMOTE_ADDR"))


class VisitViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """
    Además del CRUD estándar, expone las acciones de negocio del flujo
    de visitantes: aprobar, check-in, check-out, gafete.
    """

    queryset = Visit.objects.select_related("sede", "visitante", "anfitrion").all()
    serializer_class = VisitSerializer
    filterset_fields = ["sede", "estado"]
    role_permissions = {
        User.Rol.ADMIN_EMPRESA: (
            "list", "retrieve", "create", "update", "partial_update", "destroy",
            "autorizar", "check_in", "check_out", "gafete",
        ),
        User.Rol.SUPERVISOR: (
            "list", "retrieve", "create", "update", "partial_update", "destroy",
            "autorizar", "check_in", "check_out", "gafete",
        ),
        User.Rol.RECEPCIONISTA: (
            "list", "retrieve", "create", "update", "partial_update",
            "autorizar", "check_in", "check_out", "gafete",
        ),
        User.Rol.GUARDIA: ("list", "retrieve", "check_in", "check_out", "gafete"),
        User.Rol.OPERADOR_CENTRAL: READ_ACTIONS,
    }

    @action(detail=True, methods=["post"])
    def autorizar(self, request, pk=None):
        visita = self.get_object()
        visita.estado = Visit.Estado.AUTORIZADA
        visita.save(update_fields=["estado"])
        return Response(self.get_serializer(visita).data)

    @action(detail=True, methods=["post"])
    def check_in(self, request, pk=None):
        visita = self.get_object()
        if visita.estado not in {Visit.Estado.AUTORIZADA, Visit.Estado.PENDIENTE}:
            return Response(
                {"detail": "La visita no está en un estado válido para check-in."}, status=400
            )
        documentos_pendientes = DocumentoLegal.objects.filter(
            tenant=visita.tenant,
            activo=True,
            obligatorio_para__contains=visita.visitante.categoria,
        ).exclude(firmas__visita=visita)
        if documentos_pendientes.exists():
            return Response(
                {
                    "detail": "Faltan documentos por firmar antes del check-in.",
                    "documentos_pendientes": [d.nombre for d in documentos_pendientes],
                },
                status=400,
            )
        visita.estado = Visit.Estado.EN_CURSO
        visita.check_in_at = timezone.now()
        visita.save(update_fields=["estado", "check_in_at"])
        notificar_anfitrion(visita, evento="check_in")
        return Response(self.get_serializer(visita).data)

    @action(detail=True, methods=["post"])
    def check_out(self, request, pk=None):
        visita = self.get_object()
        visita.estado = Visit.Estado.FINALIZADA
        visita.check_out_at = timezone.now()
        visita.save(update_fields=["estado", "check_out_at"])
        return Response(self.get_serializer(visita).data)

    @action(detail=True, methods=["get"])
    def gafete(self, request, pk=None):
        """Devuelve (y persiste) la imagen QR del gafete de esta visita."""
        visita = self.get_object()
        if not visita.documento_firmado:
            archivo = generar_gafete_qr(visita)
            visita.documento_firmado.save(archivo.name, archivo, save=True)
        return Response({"gafete_url": visita.documento_firmado.url})


class InvitacionViewSet(TenantScopedViewSetMixin, viewsets.ModelViewSet):
    """CRUD de invitaciones, creado por el anfitrión/recepción (requiere login)."""

    queryset = Invitacion.objects.select_related("sede", "anfitrion").all()
    serializer_class = InvitacionSerializer
    role_permissions = {
        User.Rol.ADMIN_EMPRESA: ("list", "retrieve", "create", "update", "partial_update", "destroy"),
        User.Rol.SUPERVISOR: ("list", "retrieve", "create", "update", "partial_update", "destroy"),
        User.Rol.RECEPCIONISTA: ("list", "retrieve", "create", "update", "partial_update"),
    }


class InvitacionPublicaViewSet(viewsets.GenericViewSet):
    """
    Endpoints públicos (sin autenticación) para que el visitante confirme
    su pre-registro desde el link/QR recibido por email o WhatsApp.
    """

    queryset = Invitacion.objects.all()
    serializer_class = InvitacionPublicaSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "token"

    @action(detail=True, methods=["post"])
    def confirmar(self, request, token=None):
        invitacion = self.get_object()
        if invitacion.estado != Invitacion.Estado.ENVIADA:
            return Response({"detail": "Esta invitación ya no está disponible."}, status=400)
        if timezone.now() > invitacion.valida_hasta:
            invitacion.estado = Invitacion.Estado.EXPIRADA
            invitacion.save(update_fields=["estado"])
            return Response({"detail": "La invitación expiró."}, status=400)

        invitacion.estado = Invitacion.Estado.CONFIRMADA
        invitacion.save(update_fields=["estado"])
        return Response(self.get_serializer(invitacion).data)
