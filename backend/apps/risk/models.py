from django.db import models

from apps.tenants.mixins import TenantScopedModel
from apps.visitors.models import Sede


class EvaluacionRiesgo(TenantScopedModel):
    class Probabilidad(models.IntegerChoices):
        RARA = 1, "Rara"
        IMPROBABLE = 2, "Improbable"
        POSIBLE = 3, "Posible"
        PROBABLE = 4, "Probable"
        CASI_SEGURA = 5, "Casi segura"

    class Impacto(models.IntegerChoices):
        INSIGNIFICANTE = 1, "Insignificante"
        MENOR = 2, "Menor"
        MODERADO = 3, "Moderado"
        MAYOR = 4, "Mayor"
        CATASTROFICO = 5, "Catastrófico"

    class Estado(models.TextChoices):
        IDENTIFICADO = "identificado", "Identificado"
        EN_TRATAMIENTO = "en_tratamiento", "En tratamiento"
        MITIGADO = "mitigado", "Mitigado"
        ACEPTADO = "aceptado", "Riesgo aceptado"

    cliente_nombre = models.CharField(max_length=150)
    sede = models.ForeignKey(
        Sede, on_delete=models.SET_NULL, null=True, blank=True, related_name="evaluaciones_riesgo"
    )
    vulnerabilidad = models.CharField(max_length=180)
    descripcion = models.TextField(blank=True)
    probabilidad = models.PositiveSmallIntegerField(choices=Probabilidad.choices)
    impacto = models.PositiveSmallIntegerField(choices=Impacto.choices)
    plan_mitigacion = models.TextField()
    responsable = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="riesgos_asignados",
    )
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.IDENTIFICADO
    )
    revisado_en = models.DateField(null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-probabilidad", "-impacto", "-actualizado_en"]
        indexes = [models.Index(fields=["tenant", "estado"])]

    @property
    def puntaje(self):
        return self.probabilidad * self.impacto

    @property
    def nivel(self):
        if self.puntaje >= 20:
            return "critico"
        if self.puntaje >= 12:
            return "alto"
        if self.puntaje >= 6:
            return "medio"
        return "bajo"

    def __str__(self):
        return f"{self.vulnerabilidad} — {self.nivel}"


class IncidenteRiesgo(TenantScopedModel):
    class Severidad(models.TextChoices):
        BAJA = "baja", "Baja"
        MEDIA = "media", "Media"
        ALTA = "alta", "Alta"
        CRITICA = "critica", "Crítica"

    class Estado(models.TextChoices):
        ABIERTO = "abierto", "Abierto"
        EN_SEGUIMIENTO = "en_seguimiento", "En seguimiento"
        RESUELTO = "resuelto", "Resuelto"
        CERRADO = "cerrado", "Cerrado"

    cliente_nombre = models.CharField(max_length=150)
    sede = models.ForeignKey(
        Sede, on_delete=models.SET_NULL, null=True, blank=True, related_name="incidentes_riesgo"
    )
    evaluacion = models.ForeignKey(
        EvaluacionRiesgo, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="incidentes",
    )
    titulo = models.CharField(max_length=180)
    descripcion = models.TextField()
    severidad = models.CharField(max_length=20, choices=Severidad.choices)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.ABIERTO
    )
    ocurrido_en = models.DateTimeField()
    reportado_por = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="incidentes_reportados",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-ocurrido_en"]
        indexes = [models.Index(fields=["tenant", "estado", "severidad"])]

    def __str__(self):
        return f"{self.titulo} ({self.severidad})"


class AccionCorrectiva(TenantScopedModel):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        EN_PROGRESO = "en_progreso", "En progreso"
        COMPLETADA = "completada", "Completada"

    incidente = models.ForeignKey(
        IncidenteRiesgo, on_delete=models.CASCADE, related_name="acciones"
    )
    titulo = models.CharField(max_length=180)
    descripcion = models.TextField(blank=True)
    responsable = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="acciones_correctivas",
    )
    fecha_limite = models.DateField(null=True, blank=True)
    estado = models.CharField(
        max_length=20, choices=Estado.choices, default=Estado.PENDIENTE
    )
    completada_en = models.DateTimeField(null=True, blank=True)
    creada_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["estado", "fecha_limite", "creada_en"]
        indexes = [models.Index(fields=["tenant", "estado", "fecha_limite"])]

    def __str__(self):
        return self.titulo
