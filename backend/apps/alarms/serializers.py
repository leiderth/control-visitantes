from rest_framework import serializers

from apps.accounts.models import User
from apps.tenants.serializers import TenantScopedSerializer

from .models import AlarmEvent, DespachoLog, Sensor


class SensorSerializer(TenantScopedSerializer):
    class Meta:
        model = Sensor
        fields = ["id", "sede", "nombre", "tipo", "activo", "identificador_externo"]


class DespachoLogSerializer(TenantScopedSerializer):
    class Meta:
        model = DespachoLog
        fields = ["id", "evento", "operador", "asignado_en", "comentario"]
        read_only_fields = ["asignado_en"]


class AlarmEventSerializer(TenantScopedSerializer):
    sensor_detalle = SensorSerializer(source="sensor", read_only=True)
    despachos = DespachoLogSerializer(many=True, read_only=True)

    class Meta:
        model = AlarmEvent
        fields = [
            "id",
            "sensor",
            "sensor_detalle",
            "severidad",
            "estado",
            "disparado_en",
            "atendido_en",
            "cerrado_en",
            "notas_cierre",
            "despachos",
        ]
        read_only_fields = ["disparado_en", "atendido_en", "cerrado_en", "estado"]


class AtenderAlarmaSerializer(serializers.Serializer):
    operador = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.none(), required=False
    )
    comentario = serializers.CharField(max_length=255, allow_blank=True, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context["request"]
        tenant = request.tenant
        self.fields["operador"].queryset = User.objects.filter(
            tenant=tenant,
            is_active=True,
        )

    def validate_operador(self, operador):
        if operador.rol == User.Rol.SUPER_ADMIN:
            raise serializers.ValidationError("El operador debe pertenecer a la empresa activa.")
        return operador

    def validate(self, attrs):
        operador = attrs.get("operador", self.context["request"].user)
        evento = self.context["evento"]
        if operador.sedes.exists() and not operador.sedes.filter(pk=evento.sensor.sede_id).exists():
            raise serializers.ValidationError(
                {"operador": "El operador no tiene acceso a la sede de la alarma."}
            )
        return attrs
