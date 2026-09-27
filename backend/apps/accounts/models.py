from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Usuario del SaaS. `tenant=None` identifica al super-admin (dueño del
    SaaS); cualquier otro usuario pertenece a exactamente un tenant.
    """

    class Rol(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super-admin (dueño del SaaS)"
        ADMIN_EMPRESA = "admin_empresa", "Admin empresa de seguridad"
        SUPERVISOR = "supervisor", "Supervisor"
        OPERADOR_CENTRAL = "operador_central", "Operador de central"
        GUARDIA = "guardia", "Guardia"
        RECEPCIONISTA = "recepcionista", "Recepcionista"
        CLIENTE_FINAL = "cliente_final", "Cliente final"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="usuarios"
    )
    rol = models.CharField(max_length=30, choices=Rol.choices, default=Rol.RECEPCIONISTA)
    sedes = models.ManyToManyField(
        "visitors.Sede",
        blank=True,
        related_name="usuarios_asignados",
        help_text="Sedes visibles para este usuario (vacío = todas las del tenant)",
    )

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.rol})"
