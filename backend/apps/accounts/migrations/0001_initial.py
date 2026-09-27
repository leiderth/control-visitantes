import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("tenants", "0001_initial"),
        # Nota: dependencia circular real con visitors.Sede (para el M2M
        # `sedes`) — en el proyecto completo, `sedes` se agrega en una
        # migración separada posterior a `visitors.0001_initial` para
        # evitar el ciclo de dependencias entre apps.
    ]

    operations = [
        migrations.CreateModel(
            name="User",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("password", models.CharField(max_length=128)),
                ("last_login", models.DateTimeField(blank=True, null=True)),
                ("is_superuser", models.BooleanField(default=False)),
                ("username", models.CharField(max_length=150, unique=True)),
                ("first_name", models.CharField(blank=True, max_length=150)),
                ("last_name", models.CharField(blank=True, max_length=150)),
                ("email", models.EmailField(blank=True, max_length=254)),
                ("is_staff", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "rol",
                    models.CharField(
                        choices=[
                            ("super_admin", "Super-admin (dueño del SaaS)"),
                            ("admin_empresa", "Admin empresa de seguridad"),
                            ("supervisor", "Supervisor"),
                            ("operador_central", "Operador de central"),
                            ("guardia", "Guardia"),
                            ("recepcionista", "Recepcionista"),
                            ("cliente_final", "Cliente final"),
                        ],
                        default="recepcionista",
                        max_length=30,
                    ),
                ),
                ("tenant", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="usuarios", to="tenants.tenant")),
            ],
            options={"abstract": False},
            managers=[("objects", django.contrib.auth.models.UserManager())],
        ),
    ]
