import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0001_initial"),
        ("visitors", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentoLegal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("nombre", models.CharField(max_length=150)),
                ("contenido", models.TextField()),
                ("obligatorio_para", models.JSONField(default=list)),
                ("activo", models.BooleanField(default=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="Invitacion",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("token", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ("visitante_nombre", models.CharField(max_length=150)),
                ("visitante_documento", models.CharField(blank=True, max_length=30)),
                ("visitante_email", models.EmailField(blank=True, max_length=254)),
                ("visitante_telefono", models.CharField(blank=True, max_length=30)),
                ("requiere_aprobacion_manual", models.BooleanField(default=False)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("enviada", "Enviada"),
                            ("confirmada", "Confirmada por el visitante"),
                            ("usada", "Usada (visita creada)"),
                            ("expirada", "Expirada"),
                        ],
                        default="enviada",
                        max_length=20,
                    ),
                ),
                ("valida_desde", models.DateTimeField()),
                ("valida_hasta", models.DateTimeField()),
                ("anfitrion", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="invitaciones", to="visitors.host")),
                ("sede", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="invitaciones", to="visitors.sede")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
                ("visita_generada", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="invitacion_origen", to="visitors.visit")),
            ],
        ),
        migrations.CreateModel(
            name="FirmaDocumento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("firma_imagen", models.ImageField(upload_to="visitantes/firmas/trazo/")),
                ("ip_origen", models.GenericIPAddressField(blank=True, null=True)),
                ("firmado_en", models.DateTimeField(auto_now_add=True)),
                ("documento", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="firmas", to="visitors.documentolegal")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
                ("visita", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="firmas", to="visitors.visit")),
            ],
        ),
        migrations.AddConstraint(
            model_name="firmadocumento",
            constraint=models.UniqueConstraint(
                fields=("visita", "documento"), name="unique_firma_por_documento_y_visita"
            ),
        ),
    ]
