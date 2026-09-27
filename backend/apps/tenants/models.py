from django.db import models


class Tenant(models.Model):
    """Una empresa de seguridad cliente del SaaS (multi-tenant real)."""

    nombre = models.CharField(max_length=150)
    subdominio = models.SlugField(unique=True, help_text="Ej: 'vigilan-sa' → vigilan-sa.plataforma.com")
    logo = models.ImageField(upload_to="tenants/logos/", blank=True, null=True)
    color_primario = models.CharField(max_length=7, default="#0f172a", help_text="Hex, para white-label")
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre


class TenantModule(models.Model):
    """Feature flag persistente: qué módulos tiene activos cada tenant."""

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="modulos")
    nombre_modulo = models.CharField(
        max_length=50,
        help_text="visitors, alarms, gps, escorts, risk, cctv, access_control",
    )
    activo = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tenant", "nombre_modulo"], name="unique_modulo_por_tenant")
        ]

    def __str__(self):
        return f"{self.tenant} — {self.nombre_modulo} ({'on' if self.activo else 'off'})"
