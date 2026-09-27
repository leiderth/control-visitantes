from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Tenant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("nombre", models.CharField(max_length=150)),
                ("subdominio", models.SlugField(unique=True)),
                ("logo", models.ImageField(blank=True, null=True, upload_to="tenants/logos/")),
                ("color_primario", models.CharField(default="#0f172a", max_length=7)),
                ("activo", models.BooleanField(default=True)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="TenantModule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("nombre_modulo", models.CharField(max_length=50)),
                ("activo", models.BooleanField(default=True)),
                ("tenant", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="modulos", to="tenants.tenant")),
            ],
        ),
        migrations.AddConstraint(
            model_name="tenantmodule",
            constraint=models.UniqueConstraint(fields=("tenant", "nombre_modulo"), name="unique_modulo_por_tenant"),
        ),
    ]
