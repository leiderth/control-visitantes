from decimal import Decimal

from rest_framework import serializers

from apps.tenants.serializers import TenantScopedSerializer

from .models import AlertaPanico, CheckpointPlan, CheckpointRegistro, ServicioEscolta


class TenantRelatedModelSerializer(TenantScopedSerializer):
    def validate(self, attrs):
        tenant_id = self.context["request"].tenant.pk
        for field, value in attrs.items():
            related_objects = value if isinstance(value, (list, tuple, set)) else (value,)
            for related_object in related_objects:
                related_tenant_id = getattr(related_object, "tenant_id", tenant_id)
                if related_tenant_id != tenant_id:
                    raise serializers.ValidationError(
                        {field: "El registro relacionado debe pertenecer al tenant actual."}
                    )
        return attrs


class CheckpointRegistroSerializer(TenantRelatedModelSerializer):
    lat = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=Decimal("-90"), max_value=Decimal("90"))
    lng = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=Decimal("-180"), max_value=Decimal("180"))

    class Meta:
        model = CheckpointRegistro
        fields = ["id", "checkpoint", "lat", "lng", "registrado_en", "a_tiempo", "reportado_por"]
        read_only_fields = ["registrado_en", "a_tiempo", "reportado_por"]


class CheckpointPlanSerializer(TenantRelatedModelSerializer):
    registros = CheckpointRegistroSerializer(many=True, read_only=True)
    lat = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=Decimal("-90"), max_value=Decimal("90"))
    lng = serializers.DecimalField(max_digits=9, decimal_places=6, min_value=Decimal("-180"), max_value=Decimal("180"))
    radio_tolerancia_metros = serializers.IntegerField(min_value=1)

    class Meta:
        model = CheckpointPlan
        fields = [
            "id", "servicio", "orden", "nombre", "lat", "lng",
            "hora_estimada", "radio_tolerancia_metros", "registros",
        ]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        servicio = attrs.get("servicio", self.instance.servicio if self.instance else None)
        if servicio and servicio.estado != ServicioEscolta.Estado.PROGRAMADO:
            raise serializers.ValidationError(
                {"servicio": "Los checkpoints solo se pueden modificar antes de iniciar el servicio."}
            )
        return attrs


class AlertaPanicoSerializer(TenantRelatedModelSerializer):
    class Meta:
        model = AlertaPanico
        fields = [
            "id", "servicio", "lat", "lng", "disparado_en", "disparado_por",
            "estado", "atendido_en", "atendido_por", "cerrado_en", "notas_cierre",
        ]
        read_only_fields = [
            "disparado_en", "disparado_por", "estado", "atendido_en",
            "atendido_por", "cerrado_en",
        ]


class ServicioEscoltaSerializer(TenantRelatedModelSerializer):
    checkpoints_plan = CheckpointPlanSerializer(many=True, read_only=True)
    alertas_panico = AlertaPanicoSerializer(many=True, read_only=True)

    class Meta:
        model = ServicioEscolta
        fields = [
            "id", "cliente_nombre", "sede", "origen", "destino", "vehiculo", "personal",
            "programado_inicio", "programado_fin", "iniciado_en", "finalizado_en",
            "estado", "notas", "checkpoints_plan", "alertas_panico",
        ]
        read_only_fields = ["iniciado_en", "finalizado_en", "estado"]

    def validate(self, attrs):
        attrs = super().validate(attrs)
        campos_de_programacion = {
            "cliente_nombre", "sede", "origen", "destino", "vehiculo", "personal",
            "programado_inicio", "programado_fin",
        }
        if (
            self.instance
            and self.instance.estado != ServicioEscolta.Estado.PROGRAMADO
            and campos_de_programacion.intersection(attrs)
        ):
            raise serializers.ValidationError(
                "La programación del servicio no se puede modificar después de iniciarlo."
            )
        inicio = attrs.get("programado_inicio", self.instance.programado_inicio if self.instance else None)
        fin = attrs.get("programado_fin", self.instance.programado_fin if self.instance else None)
        if inicio and fin and fin <= inicio:
            raise serializers.ValidationError(
                {"programado_fin": "La hora de finalización debe ser posterior al inicio."}
            )
        return attrs


class ServicioEscoltaListSerializer(serializers.ModelSerializer):
    """Versión liviana para listados (sin anidar checkpoints/alertas)."""

    class Meta:
        model = ServicioEscolta
        fields = [
            "id", "cliente_nombre", "origen", "destino", "vehiculo",
            "programado_inicio", "programado_fin", "estado",
        ]


class CancelarServicioSerializer(serializers.Serializer):
    motivo = serializers.CharField(required=False, allow_blank=True)


class CoordenadasSerializer(serializers.Serializer):
    lat = serializers.DecimalField(
        max_digits=9, decimal_places=6, min_value=Decimal("-90"), max_value=Decimal("90"),
        required=False, allow_null=True,
    )
    lng = serializers.DecimalField(
        max_digits=9, decimal_places=6, min_value=Decimal("-180"), max_value=Decimal("180"),
        required=False, allow_null=True,
    )

    def validate(self, attrs):
        if ("lat" in attrs) != ("lng" in attrs):
            raise serializers.ValidationError("Debe enviar latitud y longitud juntas.")
        return attrs


class CierreAlertaPanicoSerializer(serializers.Serializer):
    notas_cierre = serializers.CharField(required=False, allow_blank=True)
