from django.db import models

from apps.tenants.mixins import TenantScopedModel
from apps.visitors.models import Sede


class Sensor(TenantScopedModel):
    """Un punto físico monitoreado: puerta, sensor de movimiento, botón de pánico, incendio."""

    class Tipo(models.TextChoices):
        PUERTA = "puerta", "Puerta / contacto"
        MOVIMIENTO = "movimiento", "Movimiento"
        PANICO = "panico", "Botón de pánico"
        INCENDIO = "incendio", "Incendio / humo"
        PERIMETRAL = "perimetral", "Perimetral"

    sede = models.ForeignKey(Sede, on_delete=models.CASCADE, related_name="sensores")
    nombre = models.CharField(max_length=150, help_text="Ej: 'Puerta principal', 'PIR pasillo 2'")
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    activo = models.BooleanField(default=True)
    # Referencia externa del sistema de alarmas real (panel DSC, Honeywell, etc).
    # La integración concreta va en el marketplace de conectores (Fase 6+).
    identificador_externo = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


class AlarmEvent(TenantScopedModel):
    """Un disparo de sensor. Es el registro central de la sala de monitoreo."""

    class Severidad(models.TextChoices):
        BAJA = "baja", "Baja"
        MEDIA = "media", "Media"
        ALTA = "alta", "Alta"
        CRITICA = "critica", "Crítica"

    class Estado(models.TextChoices):
        ACTIVA = "activa", "Activa (sin atender)"
        EN_ATENCION = "en_atencion", "En atención"
        CERRADA = "cerrada", "Cerrada"
        FALSA_ALARMA = "falsa_alarma", "Falsa alarma"

    sensor = models.ForeignKey(Sensor, on_delete=models.CASCADE, related_name="eventos")
    severidad = models.CharField(max_length=20, choices=Severidad.choices, default=Severidad.MEDIA)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVA)
    disparado_en = models.DateTimeField(auto_now_add=True)
    atendido_en = models.DateTimeField(null=True, blank=True)
    cerrado_en = models.DateTimeField(null=True, blank=True)
    notas_cierre = models.TextField(blank=True)

    class Meta:
        ordering = ["-disparado_en"]
        indexes = [models.Index(fields=["tenant", "estado", "severidad"])]

    def __str__(self):
        return f"{self.sensor} — {self.severidad} ({self.estado})"


class DespachoLog(TenantScopedModel):
    """
    Historial de asignación (CAD): quién atendió cada evento y cuándo.
    Separado de AlarmEvent para permitir reasignaciones sin perder el rastro.
    """

    evento = models.ForeignKey(AlarmEvent, on_delete=models.CASCADE, related_name="despachos")
    operador = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True)
    asignado_en = models.DateTimeField(auto_now_add=True)
    comentario = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-asignado_en"]

    def __str__(self):
        return f"{self.evento} → {self.operador}"
