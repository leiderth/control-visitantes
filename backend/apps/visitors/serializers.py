from rest_framework import serializers

from apps.tenants.serializers import TenantScopedSerializer

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


class SedeSerializer(TenantScopedSerializer):
    class Meta:
        model = Sede
        fields = ["id", "nombre", "direccion", "activa"]


class HostSerializer(TenantScopedSerializer):
    class Meta:
        model = Host
        fields = ["id", "sede", "nombre_completo", "email", "telefono", "notificar_por"]

    def validate(self, attrs):
        sede = attrs.get("sede", getattr(self.instance, "sede", None))
        if sede is not None and sede.tenant_id != self.context["request"].tenant.pk:
            raise serializers.ValidationError({"sede": "La sede debe pertenecer a la empresa activa."})
        return attrs


class VisitorSerializer(TenantScopedSerializer):
    en_watchlist = serializers.SerializerMethodField()

    class Meta:
        model = Visitor
        fields = [
            "id",
            "documento_tipo",
            "documento_numero",
            "nombre_completo",
            "empresa",
            "categoria",
            "foto",
            "documento_escaneado",
            "en_watchlist",
        ]

    def get_en_watchlist(self, obj) -> bool:
        return WatchlistEntry.objects.filter(
            tenant=obj.tenant, documento_numero=obj.documento_numero
        ).exists()


class WatchlistEntrySerializer(TenantScopedSerializer):
    class Meta:
        model = WatchlistEntry
        fields = ["id", "documento_numero", "nombre_completo", "tipo", "motivo", "registrado_por"]
        read_only_fields = ["registrado_por"]


class VisitSerializer(TenantScopedSerializer):
    visitante_detalle = VisitorSerializer(source="visitante", read_only=True)

    class Meta:
        model = Visit
        fields = [
            "id",
            "codigo_qr",
            "sede",
            "visitante",
            "visitante_detalle",
            "anfitrion",
            "estado",
            "hora_autorizada_desde",
            "hora_autorizada_hasta",
            "check_in_at",
            "check_out_at",
            "documento_firmado",
            "firmado_en",
        ]
        read_only_fields = ["codigo_qr", "check_in_at", "check_out_at", "firmado_en", "estado"]

    def validate(self, attrs):
        sede = attrs.get("sede", getattr(self.instance, "sede", None))
        anfitrion = attrs.get("anfitrion", getattr(self.instance, "anfitrion", None))
        if anfitrion is not None and sede is not None and anfitrion.sede_id != sede.pk:
            raise serializers.ValidationError(
                {"anfitrion": "El anfitrión debe pertenecer a la sede seleccionada."}
            )
        return attrs


class InvitacionSerializer(TenantScopedSerializer):
    class Meta:
        model = Invitacion
        fields = [
            "id",
            "token",
            "sede",
            "anfitrion",
            "visitante_nombre",
            "visitante_documento",
            "visitante_email",
            "visitante_telefono",
            "requiere_aprobacion_manual",
            "estado",
            "valida_desde",
            "valida_hasta",
            "visita_generada",
        ]
        read_only_fields = ["token", "estado", "visita_generada"]

    def validate(self, attrs):
        sede = attrs.get("sede", getattr(self.instance, "sede", None))
        anfitrion = attrs.get("anfitrion", getattr(self.instance, "anfitrion", None))
        if anfitrion is not None and sede is not None and anfitrion.sede_id != sede.pk:
            raise serializers.ValidationError(
                {"anfitrion": "El anfitrión debe pertenecer a la sede seleccionada."}
            )
        return attrs


class InvitacionPublicaSerializer(serializers.ModelSerializer):
    """Vista reducida para la confirmación pública (sin login) por link/QR."""

    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True)
    anfitrion_nombre = serializers.CharField(source="anfitrion.nombre_completo", read_only=True)

    class Meta:
        model = Invitacion
        fields = [
            "token",
            "sede_nombre",
            "anfitrion_nombre",
            "visitante_nombre",
            "estado",
            "valida_desde",
            "valida_hasta",
        ]


class DocumentoLegalSerializer(TenantScopedSerializer):
    class Meta:
        model = DocumentoLegal
        fields = ["id", "nombre", "contenido", "obligatorio_para", "activo"]


class FirmaDocumentoSerializer(TenantScopedSerializer):
    class Meta:
        model = FirmaDocumento
        fields = ["id", "visita", "documento", "firma_imagen", "ip_origen", "firmado_en"]
        read_only_fields = ["ip_origen", "firmado_en"]

    def validate(self, attrs):
        visita = attrs.get("visita", getattr(self.instance, "visita", None))
        documento = attrs.get("documento", getattr(self.instance, "documento", None))
        if visita is not None and documento is not None and visita.tenant_id != documento.tenant_id:
            raise serializers.ValidationError(
                {"documento": "La visita y el documento deben pertenecer a la misma empresa."}
            )
        return attrs
