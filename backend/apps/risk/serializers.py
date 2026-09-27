from rest_framework import serializers

from apps.tenants.serializers import TenantScopedSerializer

from .models import AccionCorrectiva, EvaluacionRiesgo, IncidenteRiesgo


class TenantRelatedModelSerializer(TenantScopedSerializer):
    def validate(self, attrs):
        tenant_id = self.context["request"].tenant.pk
        for field, value in attrs.items():
            values = value if isinstance(value, (list, tuple, set)) else (value,)
            for related_object in values:
                if hasattr(related_object, "tenant_id") and related_object.tenant_id != tenant_id:
                    raise serializers.ValidationError(
                        {field: "El registro relacionado debe pertenecer al tenant actual."}
                    )
        return attrs


class EvaluacionRiesgoSerializer(TenantRelatedModelSerializer):
    puntaje = serializers.IntegerField(read_only=True)
    nivel = serializers.CharField(read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)

    class Meta:
        model = EvaluacionRiesgo
        fields = [
            "id", "cliente_nombre", "sede", "vulnerabilidad", "descripcion",
            "probabilidad", "impacto", "puntaje", "nivel", "plan_mitigacion",
            "responsable", "estado", "estado_display", "revisado_en",
            "creado_en", "actualizado_en",
        ]
        read_only_fields = ["creado_en", "actualizado_en"]


class AccionCorrectivaSerializer(TenantRelatedModelSerializer):
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    responsable_nombre = serializers.SerializerMethodField()

    class Meta:
        model = AccionCorrectiva
        fields = [
            "id", "incidente", "titulo", "descripcion", "responsable",
            "responsable_nombre", "fecha_limite", "estado", "estado_display",
            "completada_en", "creada_en",
        ]
        read_only_fields = ["estado", "completada_en", "creada_en"]

    def get_responsable_nombre(self, obj):
        if not obj.responsable:
            return None
        return obj.responsable.get_full_name() or obj.responsable.username

    def validate(self, attrs):
        attrs = super().validate(attrs)
        incidente = attrs.get("incidente", self.instance.incidente if self.instance else None)
        if incidente and incidente.estado in {
            IncidenteRiesgo.Estado.RESUELTO,
            IncidenteRiesgo.Estado.CERRADO,
        }:
            raise serializers.ValidationError(
                {"incidente": "No se pueden modificar acciones de un incidente resuelto o cerrado."}
            )
        return attrs


class IncidenteRiesgoSerializer(TenantRelatedModelSerializer):
    acciones = AccionCorrectivaSerializer(many=True, read_only=True)
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    sede_nombre = serializers.CharField(source="sede.nombre", read_only=True, default=None)
    reportado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = IncidenteRiesgo
        fields = [
            "id", "cliente_nombre", "sede", "sede_nombre", "evaluacion",
            "titulo", "descripcion", "severidad", "estado", "estado_display",
            "ocurrido_en", "reportado_por", "reportado_por_nombre",
            "acciones", "creado_en", "actualizado_en",
        ]
        read_only_fields = ["estado", "reportado_por", "creado_en", "actualizado_en"]

    def get_reportado_por_nombre(self, obj):
        if not obj.reportado_por:
            return None
        return obj.reportado_por.get_full_name() or obj.reportado_por.username

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if self.instance and self.instance.estado == IncidenteRiesgo.Estado.CERRADO and attrs:
            raise serializers.ValidationError("No se puede modificar un incidente cerrado.")
        sede = attrs.get("sede", self.instance.sede if self.instance else None)
        evaluacion = attrs.get("evaluacion", self.instance.evaluacion if self.instance else None)
        cliente_nombre = attrs.get(
            "cliente_nombre", self.instance.cliente_nombre if self.instance else None
        )
        if evaluacion and cliente_nombre and evaluacion.cliente_nombre != cliente_nombre:
            raise serializers.ValidationError(
                {"evaluacion": "La evaluación debe corresponder al mismo cliente del incidente."}
            )
        if sede and evaluacion and evaluacion.sede_id not in (None, sede.pk):
            raise serializers.ValidationError(
                {"evaluacion": "La evaluación debe corresponder a la sede del incidente."}
            )
        return attrs
