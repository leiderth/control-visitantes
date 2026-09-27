from django.db import models

from apps.tenants.mixins import TenantScopedModel
from apps.visitors.models import Sede


class ServicioEscolta(TenantScopedModel):
    """
    Un servicio de escolta programado: de dónde a dónde, con qué vehículo
    y qué personal, y en qué estado va. Reutiliza `apps.gps.Vehiculo` en vez
    de duplicar el catálogo de vehículos (mismo vehículo puede usarse para
    rastreo GPS general y para un servicio de escolta puntual).
    """

    class Estado(models.TextChoices):
        PROGRAMADO = "programado", "Programado"
        EN_CURSO = "en_curso", "En curso"
        FINALIZADO = "finalizado", "Finalizado"
        CANCELADO = "cancelado", "Cancelado"

    cliente_nombre = models.CharField(max_length=150)
    sede = models.ForeignKey(
        Sede, on_delete=models.SET_NULL, null=True, blank=True, related_name="servicios_escolta",
        help_text="Opcional — solo si el cliente ya tiene una sede registrada en Visitantes",
    )
    origen = models.CharField(max_length=255)
    destino = models.CharField(max_length=255)
    vehiculo = models.ForeignKey(
        "gps.Vehiculo", on_delete=models.SET_NULL, null=True, blank=True, related_name="servicios_escolta",
    )
    personal = models.ManyToManyField(
        "accounts.User", blank=True, related_name="servicios_escolta_asignado",
        help_text="Guardias/escoltas asignados al servicio",
    )
    programado_inicio = models.DateTimeField()
    programado_fin = models.DateTimeField()
    iniciado_en = models.DateTimeField(null=True, blank=True)
    finalizado_en = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PROGRAMADO)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ["-programado_inicio"]
        indexes = [models.Index(fields=["tenant", "estado"])]

    def __str__(self):
        return f"{self.cliente_nombre}: {self.origen} → {self.destino} ({self.estado})"


class CheckpointPlan(TenantScopedModel):
    """Un punto de la ruta que se espera que el servicio confirme al pasar."""

    servicio = models.ForeignKey(ServicioEscolta, on_delete=models.CASCADE, related_name="checkpoints_plan")
    orden = models.PositiveIntegerField()
    nombre = models.CharField(max_length=150)
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)
    hora_estimada = models.DateTimeField(null=True, blank=True)
    radio_tolerancia_metros = models.PositiveIntegerField(default=150)

    class Meta:
        ordering = ["servicio", "orden"]
        constraints = [
            models.UniqueConstraint(fields=["servicio", "orden"], name="unique_orden_por_servicio")
        ]

    def __str__(self):
        return f"{self.servicio} — checkpoint {self.orden}: {self.nombre}"


class CheckpointRegistro(TenantScopedModel):
    """
    Confirmación real de paso por un `CheckpointPlan`. `a_tiempo` se calcula
    en `services.registrar_checkpoint` comparando contra `hora_estimada` +
    una tolerancia — no se deja en manos del cliente que reporta.
    """

    checkpoint = models.ForeignKey(CheckpointPlan, on_delete=models.CASCADE, related_name="registros")
    lat = models.DecimalField(max_digits=9, decimal_places=6)
    lng = models.DecimalField(max_digits=9, decimal_places=6)
    registrado_en = models.DateTimeField(auto_now_add=True)
    a_tiempo = models.BooleanField(default=True)
    reportado_por = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )

    class Meta:
        ordering = ["-registrado_en"]

    def __str__(self):
        return f"{self.checkpoint} @ {self.registrado_en}"


class AlertaPanico(TenantScopedModel):
    """
    Botón de pánico específico de un servicio de escolta. Se mantiene como
    modelo propio (no un `AlarmEvent` de `apps.alarms`) porque nace de una
    acción del guardia en campo, no de un sensor físico — el motor de
    correlación de riesgo (Fase 6+) es el que cruzará ambos si coinciden en
    tiempo/sede, sin que un módulo dependa del otro.
    """

    class Estado(models.TextChoices):
        ACTIVA = "activa", "Activa (sin atender)"
        ATENDIDA = "atendida", "Atendida"
        CERRADA = "cerrada", "Cerrada"

    servicio = models.ForeignKey(ServicioEscolta, on_delete=models.CASCADE, related_name="alertas_panico")
    lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    disparado_en = models.DateTimeField(auto_now_add=True)
    disparado_por = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ACTIVA)
    atendido_en = models.DateTimeField(null=True, blank=True)
    atendido_por = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    cerrado_en = models.DateTimeField(null=True, blank=True)
    notas_cierre = models.TextField(blank=True)

    class Meta:
        ordering = ["-disparado_en"]
        indexes = [models.Index(fields=["tenant", "estado"])]

    def __str__(self):
        return f"Pánico — {self.servicio} ({self.estado})"
