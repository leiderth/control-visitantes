import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenants", "0001_initial"),
        ("visitors", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Sensor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("nombre", models.CharField(max_length=150)),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("puerta", "Puerta / contacto"),
                            ("movimiento", "Movimiento"),
                            ("panico", "Botón de pánico"),
                            ("incendio", "Incendio / humo"),
                            ("perimetral", "Perimetral"),
                        ],
                        max_length=20,
                    ),
                ),
                ("activo", models.BooleanField(default=True)),
                ("identificador_externo", models.CharField(blank=True, max_length=100)),
                ("sede", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sensores", to="visitors.sede")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="AlarmEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                (
                    "severidad",
                    models.CharField(
                        choices=[("baja", "Baja"), ("media", "Media"), ("alta", "Alta"), ("critica", "Crítica")],
                        default="media",
                        max_length=20,
                    ),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("activa", "Activa (sin atender)"),
                            ("en_atencion", "En atención"),
                            ("cerrada", "Cerrada"),
                            ("falsa_alarma", "Falsa alarma"),
                        ],
                        default="activa",
                        max_length=20,
                    ),
                ),
                ("disparado_en", models.DateTimeField(auto_now_add=True)),
                ("atendido_en", models.DateTimeField(blank=True, null=True)),
                ("cerrado_en", models.DateTimeField(blank=True, null=True)),
                ("notas_cierre", models.TextField(blank=True)),
                ("sensor", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="eventos", to="alarms.sensor")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
            ],
            options={"ordering": ["-disparado_en"]},
        ),
        migrations.CreateModel(
            name="DespachoLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("asignado_en", models.DateTimeField(auto_now_add=True)),
                ("comentario", models.CharField(blank=True, max_length=255)),
                ("evento", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="despachos", to="alarms.alarmevent")),
                ("operador", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
            ],
            options={"ordering": ["-asignado_en"]},
        ),
        migrations.AddIndex(
            model_name="alarmevent",
            index=models.Index(fields=["tenant", "estado", "severidad"], name="alarms_alar_tenant__idx"),
        ),
    ]
