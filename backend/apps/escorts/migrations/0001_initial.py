import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = [
        ("tenants", "0001_initial"),
        ("visitors", "0001_initial"),
        ("gps", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ServicioEscolta",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("cliente_nombre", models.CharField(max_length=150)),
                ("origen", models.CharField(max_length=255)),
                ("destino", models.CharField(max_length=255)),
                ("programado_inicio", models.DateTimeField()),
                ("programado_fin", models.DateTimeField()),
                ("iniciado_en", models.DateTimeField(blank=True, null=True)),
                ("finalizado_en", models.DateTimeField(blank=True, null=True)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("programado", "Programado"),
                            ("en_curso", "En curso"),
                            ("finalizado", "Finalizado"),
                            ("cancelado", "Cancelado"),
                        ],
                        default="programado",
                        max_length=20,
                    ),
                ),
                ("notas", models.TextField(blank=True)),
                (
                    "personal",
                    models.ManyToManyField(
                        blank=True, related_name="servicios_escolta_asignado", to=settings.AUTH_USER_MODEL
                    ),
                ),
                (
                    "sede",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name="servicios_escolta", to="visitors.sede",
                    ),
                ),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
                (
                    "vehiculo",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name="servicios_escolta", to="gps.vehiculo",
                    ),
                ),
            ],
            options={"ordering": ["-programado_inicio"]},
        ),
        migrations.CreateModel(
            name="CheckpointPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("orden", models.PositiveIntegerField()),
                ("nombre", models.CharField(max_length=150)),
                ("lat", models.DecimalField(decimal_places=6, max_digits=9)),
                ("lng", models.DecimalField(decimal_places=6, max_digits=9)),
                ("hora_estimada", models.DateTimeField(blank=True, null=True)),
                ("radio_tolerancia_metros", models.PositiveIntegerField(default=150)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
                (
                    "servicio",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="checkpoints_plan", to="escorts.servicioescolta",
                    ),
                ),
            ],
            options={"ordering": ["servicio", "orden"]},
        ),
        migrations.CreateModel(
            name="CheckpointRegistro",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("lat", models.DecimalField(decimal_places=6, max_digits=9)),
                ("lng", models.DecimalField(decimal_places=6, max_digits=9)),
                ("registrado_en", models.DateTimeField(auto_now_add=True)),
                ("a_tiempo", models.BooleanField(default=True)),
                (
                    "checkpoint",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="registros", to="escorts.checkpointplan",
                    ),
                ),
                (
                    "reportado_por",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+", to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
            ],
            options={"ordering": ["-registrado_en"]},
        ),
        migrations.CreateModel(
            name="AlertaPanico",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("lat", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("lng", models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ("disparado_en", models.DateTimeField(auto_now_add=True)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("activa", "Activa (sin atender)"),
                            ("atendida", "Atendida"),
                            ("cerrada", "Cerrada"),
                        ],
                        default="activa",
                        max_length=20,
                    ),
                ),
                ("atendido_en", models.DateTimeField(blank=True, null=True)),
                ("cerrado_en", models.DateTimeField(blank=True, null=True)),
                ("notas_cierre", models.TextField(blank=True)),
                (
                    "atendido_por",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+", to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "disparado_por",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+", to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "servicio",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="alertas_panico", to="escorts.servicioescolta",
                    ),
                ),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
            ],
            options={"ordering": ["-disparado_en"]},
        ),
        migrations.AddConstraint(
            model_name="checkpointplan",
            constraint=models.UniqueConstraint(fields=("servicio", "orden"), name="unique_orden_por_servicio"),
        ),
        migrations.AddIndex(
            model_name="servicioescolta",
            index=models.Index(fields=["tenant", "estado"], name="escorts_ser_tenant__f11a4f_idx"),
        ),
        migrations.AddIndex(
            model_name="alertapanico",
            index=models.Index(fields=["tenant", "estado"], name="escorts_ale_tenant__6cbd8e_idx"),
        ),
    ]
