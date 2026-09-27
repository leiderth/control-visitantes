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
            name="Vehiculo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("placa", models.CharField(blank=True, max_length=15)),
                ("tipo", models.CharField(choices=[("moto", "Moto"), ("carro", "Carro/camioneta"), ("a_pie", "Guardia a pie (dispositivo móvil)")], max_length=10)),
                ("activo", models.BooleanField(default=True)),
                ("asignado_a", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vehiculos", to=settings.AUTH_USER_MODEL)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="DispositivoGPS",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("identificador_externo", models.CharField(max_length=100, unique=True)),
                ("activo", models.BooleanField(default=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
                ("vehiculo", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="dispositivo", to="gps.vehiculo")),
            ],
        ),
        migrations.CreateModel(
            name="Geocerca",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("nombre", models.CharField(max_length=150)),
                ("centro_lat", models.DecimalField(decimal_places=6, max_digits=9)),
                ("centro_lng", models.DecimalField(decimal_places=6, max_digits=9)),
                ("radio_metros", models.PositiveIntegerField(default=200)),
                ("activa", models.BooleanField(default=True)),
                ("sede", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="geocercas", to="visitors.sede")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
            ],
        ),
        migrations.CreateModel(
            name="PosicionGPS",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("lat", models.DecimalField(decimal_places=6, max_digits=9)),
                ("lng", models.DecimalField(decimal_places=6, max_digits=9)),
                ("velocidad_kmh", models.FloatField(blank=True, null=True)),
                ("capturado_en", models.DateTimeField()),
                ("dispositivo", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="posiciones", to="gps.dispositivogps")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
            ],
            options={"ordering": ["-capturado_en"]},
        ),
        migrations.CreateModel(
            name="GeocercaEvento",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("tipo", models.CharField(choices=[("entrada", "Entrada"), ("salida", "Salida")], max_length=10)),
                ("ocurrido_en", models.DateTimeField(auto_now_add=True)),
                ("geocerca", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="eventos", to="gps.geocerca")),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="tenants.tenant")),
                ("vehiculo", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="eventos_geocerca", to="gps.vehiculo")),
            ],
            options={"ordering": ["-ocurrido_en"]},
        ),
        migrations.AddIndex(
            model_name="posiciongps",
            index=models.Index(fields=["dispositivo", "-capturado_en"], name="gps_posicio_disposi_idx"),
        ),
    ]
