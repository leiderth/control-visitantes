import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenants", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Sede",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("nombre", models.CharField(max_length=150)),
                ("direccion", models.CharField(blank=True, max_length=255)),
                ("activa", models.BooleanField(default=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
            ],
            options={"ordering": ["nombre"]},
        ),
        migrations.CreateModel(
            name="Visitor",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("documento_tipo", models.CharField(default="CC", max_length=10)),
                ("documento_numero", models.CharField(db_index=True, max_length=30)),
                ("nombre_completo", models.CharField(max_length=150)),
                ("empresa", models.CharField(blank=True, max_length=150)),
                (
                    "categoria",
                    models.CharField(
                        choices=[
                            ("normal", "Visitante normal"),
                            ("contratista", "Contratista"),
                            ("proveedor", "Proveedor"),
                            ("mensajeria", "Mensajería / delivery"),
                            ("vip", "VIP"),
                            ("temporal", "Personal temporal"),
                        ],
                        default="normal",
                        max_length=20,
                    ),
                ),
                ("foto", models.ImageField(blank=True, null=True, upload_to="visitantes/fotos/")),
                ("documento_escaneado", models.FileField(blank=True, null=True, upload_to="visitantes/documentos/")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="Host",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("nombre_completo", models.CharField(max_length=150)),
                ("email", models.EmailField(max_length=254)),
                ("telefono", models.CharField(blank=True, max_length=30)),
                ("notificar_por", models.JSONField(default=list)),
                ("sede", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="hosts", to="visitors.sede")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="WatchlistEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("documento_numero", models.CharField(db_index=True, max_length=30)),
                ("nombre_completo", models.CharField(max_length=150)),
                ("tipo", models.CharField(choices=[("blacklist", "Lista negra"), ("watchlist", "Lista de vigilancia")], max_length=20)),
                ("motivo", models.TextField()),
                ("registrado_por", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="Visit",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("codigo_qr", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("pendiente", "Pendiente de aprobación"),
                            ("autorizada", "Autorizada"),
                            ("en_curso", "En curso (check-in hecho)"),
                            ("finalizada", "Finalizada (check-out hecho)"),
                            ("excedida", "Tiempo excedido"),
                            ("rechazada", "Rechazada"),
                        ],
                        default="pendiente",
                        max_length=20,
                    ),
                ),
                ("hora_autorizada_desde", models.DateTimeField()),
                ("hora_autorizada_hasta", models.DateTimeField()),
                ("check_in_at", models.DateTimeField(blank=True, null=True)),
                ("check_out_at", models.DateTimeField(blank=True, null=True)),
                ("documento_firmado", models.FileField(blank=True, null=True, upload_to="visitantes/firmas/")),
                ("firmado_en", models.DateTimeField(blank=True, null=True)),
                ("anfitrion", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="visitas", to="visitors.host")),
                ("sede", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="visitas", to="visitors.sede")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
                ("visitante", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="visitas", to="visitors.visitor")),
            ],
            options={"ordering": ["-hora_autorizada_desde"]},
        ),
        migrations.AddConstraint(
            model_name="visitor",
            constraint=models.UniqueConstraint(
                fields=("tenant", "documento_tipo", "documento_numero"),
                name="unique_documento_por_tenant",
            ),
        ),
        migrations.AddIndex(
            model_name="visit",
            index=models.Index(fields=["tenant", "sede", "estado"], name="visitors_vi_tenant__idx"),
        ),
    ]
