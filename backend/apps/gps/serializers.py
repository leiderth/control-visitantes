from apps.tenants.serializers import TenantScopedSerializer

from .models import DispositivoGPS, Geocerca, GeocercaEvento, PosicionGPS, Vehiculo


class VehiculoSerializer(TenantScopedSerializer):
    class Meta:
        model = Vehiculo
        fields = ["id", "placa", "tipo", "asignado_a", "activo"]


class DispositivoGPSSerializer(TenantScopedSerializer):
    class Meta:
        model = DispositivoGPS
        fields = ["id", "vehiculo", "identificador_externo", "activo"]


class PosicionGPSSerializer(TenantScopedSerializer):
    class Meta:
        model = PosicionGPS
        fields = ["id", "dispositivo", "lat", "lng", "velocidad_kmh", "capturado_en"]


class GeocercaSerializer(TenantScopedSerializer):
    class Meta:
        model = Geocerca
        fields = ["id", "sede", "nombre", "centro_lat", "centro_lng", "radio_metros", "activa"]


class GeocercaEventoSerializer(TenantScopedSerializer):
    class Meta:
        model = GeocercaEvento
        fields = ["id", "geocerca", "vehiculo", "tipo", "ocurrido_en"]
