from django.db import models

from apps.tenants.mixins import TenantScopedModel
from apps.visitors.models import Sede


class Vehiculo(TenantScopedModel):
    class Tipo(models.TextChoices):
        MOTO = "moto", "Moto"
        CARRO = "carro", "Carro/camioneta"
        A_PIE = "a_pie", "Guardia a pie (dispositivo móvil)"

    placa = models.CharField(max_length=15, blank=True, help_text="Vacío si es guardia a pie")
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    asignado_a = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="vehiculos"
    )
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.placa or f"Dispositivo de {self.asignado_a}"


class DispositivoGPS(TenantScopedModel):
    """El hardware/app que reporta posición. Separado de Vehiculo para poder
    reasignar un dispositivo a otro vehículo sin perder el historial."""

    vehiculo = models.OneToOneField(Vehiculo, on_delete=models.CASCADE, related_name="dispositivo")
    identificador_externo = models.CharField(max_length=100, unique=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"GPS de {self.vehiculo}"


class PosicionGPS(TenantScopedModel):
    """Un punto de la traza. Se crea uno por cada reporte del dispositivo (alta frecuencia)."""

    dispositivo = models.ForeignKey(DispositivoGPS, on_delete=models.CASCADE, related_name="posiciones")
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)
    velocidad_kmh = models.FloatField(null=True, blank=True)
    capturado_en = models.DateTimeField()

    class Meta:
        ordering = ["-capturado_en"]
        indexes = [models.Index(fields=["dispositivo", "-capturado_en"])]

    def __str__(self):
        return f"{self.dispositivo} @ ({self.lat}, {self.lng})"


class Geocerca(TenantScopedModel):
    """
    Zona circular autorizada alrededor de una sede (radio en metros).
    Se usa un círculo (no polígono) para mantener el cálculo de
    entrada/salida en una simple distancia haversine — suficiente para
    la mayoría de sedes; un polígono real queda para cuando se necesite.
    """

    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name="geocercas")
    nombre = models.CharField(max_length=150)
    centro_lat = models.DecimalField(max_digits=9, decimal_places=6)
    centro_lng = models.DecimalField(max_digits=9, decimal_places=6)
    radio_metros = models.PositiveIntegerField(default=200)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class GeocercaEvento(TenantScopedModel):
    class Tipo(models.TextChoices):
        ENTRADA = "entrada", "Entrada"
        SALIDA = "salida", "Salida"

    geocerca = models.ForeignKey(Geocerca, on_delete=models.CASCADE, related_name="eventos")
    vehiculo = models.ForeignKey(Vehiculo, on_delete=models.CASCADE, related_name="eventos_geocerca")
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    ocurrido_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-ocurrido_en"]

    def __str__(self):
        return f"{self.vehiculo} — {self.tipo} de {self.geocerca}"
