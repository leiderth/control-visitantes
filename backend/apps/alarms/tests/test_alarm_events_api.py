import pytest
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.alarms.models import AlarmEvent, Sensor
from apps.tenants.models import Tenant
from apps.visitors.models import Sede


@pytest.mark.django_db
def test_flujo_atender_y_cerrar_evento(tenant, admin_user):
    client = APIClient()
    client.force_authenticate(admin_user)
    client.defaults["HTTP_X_TENANT_ID"] = str(tenant.pk)

    sede = Sede.objects.create(tenant=tenant, nombre="Torre Norte")
    sensor = Sensor.objects.create(tenant=tenant, sede=sede, nombre="Puerta principal", tipo="puerta")
    evento = AlarmEvent.objects.create(tenant=tenant, sensor=sensor, severidad="alta")

    resp = client.post(f"/api/alarms/eventos/{evento.id}/atender/", {"comentario": "Enviando guardia"})
    assert resp.status_code == 200
    assert resp.data["estado"] == "en_atencion"
    assert len(resp.data["despachos"]) == 1

    resp = client.post(f"/api/alarms/eventos/{evento.id}/cerrar/", {"notas_cierre": "Puerta forzada por mantenimiento"})
    assert resp.status_code == 200
    assert resp.data["estado"] == "cerrada"


@pytest.mark.django_db
def test_marcar_falsa_alarma(tenant, admin_user):
    client = APIClient()
    client.force_authenticate(admin_user)
    client.defaults["HTTP_X_TENANT_ID"] = str(tenant.pk)

    sede = Sede.objects.create(tenant=tenant, nombre="Torre Norte")
    sensor = Sensor.objects.create(tenant=tenant, sede=sede, nombre="PIR pasillo 2", tipo="movimiento")
    evento = AlarmEvent.objects.create(tenant=tenant, sensor=sensor, severidad="baja")

    resp = client.post(f"/api/alarms/eventos/{evento.id}/marcar_falsa_alarma/")
    assert resp.status_code == 200
    assert resp.data["estado"] == "falsa_alarma"


@pytest.mark.django_db
def test_despacho_no_acepta_operador_de_otro_tenant(tenant, admin_user):
    otro_tenant = Tenant.objects.create(nombre="Otra empresa", subdominio="otra-empresa")
    operador_ajeno = User.objects.create_user(
        username="operador-ajeno",
        password="password",
        tenant=otro_tenant,
        rol=User.Rol.OPERADOR_CENTRAL,
    )
    sede = Sede.objects.create(tenant=tenant, nombre="Torre Norte")
    sensor = Sensor.objects.create(tenant=tenant, sede=sede, nombre="Puerta", tipo="puerta")
    evento = AlarmEvent.objects.create(tenant=tenant, sensor=sensor, severidad="alta")
    client = APIClient()
    client.force_authenticate(admin_user)
    client.defaults["HTTP_X_TENANT_ID"] = str(tenant.pk)

    response = client.post(
        f"/api/alarms/eventos/{evento.pk}/atender/",
        {"operador": operador_ajeno.pk},
        format="json",
    )

    assert response.status_code == 400
    assert not evento.despachos.exists()


@pytest.mark.django_db
def test_recepcionista_no_puede_cerrar_alarmas(tenant):
    recepcionista = User.objects.create_user(
        username="recepcion",
        password="password",
        tenant=tenant,
        rol=User.Rol.RECEPCIONISTA,
    )
    sede = Sede.objects.create(tenant=tenant, nombre="Torre Norte")
    sensor = Sensor.objects.create(tenant=tenant, sede=sede, nombre="Puerta", tipo="puerta")
    evento = AlarmEvent.objects.create(tenant=tenant, sensor=sensor, severidad="alta")
    client = APIClient()
    client.force_authenticate(recepcionista)
    client.defaults["HTTP_X_TENANT_ID"] = str(tenant.pk)

    response = client.post(f"/api/alarms/eventos/{evento.pk}/cerrar/")

    assert response.status_code == 403
    evento.refresh_from_db()
    assert evento.estado == AlarmEvent.Estado.ACTIVA
