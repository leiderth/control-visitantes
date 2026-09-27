from django.contrib import admin

from .models import DocumentoLegal, FirmaDocumento, Host, Invitacion, Sede, Visit, Visitor, WatchlistEntry


@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ["nombre", "tenant", "activa"]
    list_filter = ["tenant", "activa"]


@admin.register(Host)
class HostAdmin(admin.ModelAdmin):
    list_display = ["nombre_completo", "sede", "email"]


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ["nombre_completo", "documento_numero", "categoria", "tenant"]
    search_fields = ["documento_numero", "nombre_completo"]


@admin.register(WatchlistEntry)
class WatchlistEntryAdmin(admin.ModelAdmin):
    list_display = ["nombre_completo", "tipo", "documento_numero", "tenant"]
    list_filter = ["tipo"]


@admin.register(Visit)
class VisitAdmin(admin.ModelAdmin):
    list_display = ["visitante", "sede", "estado", "hora_autorizada_desde"]
    list_filter = ["estado", "sede"]


@admin.register(Invitacion)
class InvitacionAdmin(admin.ModelAdmin):
    list_display = ["visitante_nombre", "sede", "anfitrion", "estado", "valida_hasta"]
    list_filter = ["estado", "sede"]


@admin.register(DocumentoLegal)
class DocumentoLegalAdmin(admin.ModelAdmin):
    list_display = ["nombre", "activo", "tenant"]


@admin.register(FirmaDocumento)
class FirmaDocumentoAdmin(admin.ModelAdmin):
    list_display = ["visita", "documento", "firmado_en"]
