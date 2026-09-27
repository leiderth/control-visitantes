from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.escorts.models import AlertaPanico, CheckpointPlan, ServicioEscolta
from apps.gps.models import Vehiculo
from apps.tenants.models import Tenant


@pytest.fixture
def api_client(admin_user, tenant):
    client = APIClient()
    client.force_authenticate(admin_user)
    client.defaults["HTTP_X_TENANT_ID"] = str(tenant.pk)
    return client


@pytest.fixture
def servicio(tenant):
    inicio = timezone.now()
    return ServicioEscolta.objects.create(
        tenant=tenant,
        cliente_nombre="Banco Andino",
        origen="Bodega central",
        destino="Sucursal El Poblado",
        programado_inicio=inicio,
        programado_fin=inicio + timedelta(hours=2),
    )


@pytest.mark.django_db
def test_servicio_solo_acepta_transiciones_validas(api_client, servicio):
    finalizar_url = reverse("servicio-escolta-finalizar", args=[servicio.pk])
    assert api_client.post(finalizar_url).status_code == 400

    iniciar_url = reverse("servicio-escolta-iniciar", args=[servicio.pk])
    assert api_client.post(iniciar_url).status_code == 200
    assert api_client.post(iniciar_url).status_code == 400
    assert api_client.post(finalizar_url).status_code == 200


@pytest.mark.django_db
def test_no_se_puede_reprogramar_ni_eliminar_un_servicio_iniciado(api_client, servicio):
    servicio.estado = ServicioEscolta.Estado.EN_CURSO
    servicio.save(update_fields=["estado"])
    detalle_url = reverse("servicio-escolta-detail", args=[servicio.pk])

    assert api_client.patch(detalle_url, {"origen": "Otro origen"}).status_code == 400
    assert api_client.delete(detalle_url).status_code == 400


@pytest.mark.django_db
def test_panico_solo_se_dispara_en_servicio_en_curso(api_client, servicio):
    panico_url = reverse("servicio-escolta-panico", args=[servicio.pk])
    assert api_client.post(panico_url, {"lat": 6.25, "lng": -75.56}).status_code == 400
    assert api_client.post(panico_url, {"lat": 6.25}).status_code == 400

    api_client.post(reverse("servicio-escolta-iniciar", args=[servicio.pk]))
    respuesta = api_client.post(panico_url, {"lat": 6.25, "lng": -75.56})

    assert respuesta.status_code == 201
    assert respuesta.data["estado"] == AlertaPanico.Estado.ACTIVA
    assert AlertaPanico.objects.filter(servicio=servicio).count() == 1


@pytest.mark.django_db
def test_ciclo_de_atencion_y_cierre_de_panico(api_client, servicio, tenant):
    servicio.estado = ServicioEscolta.Estado.EN_CURSO
    servicio.save(update_fields=["estado"])
    alerta = AlertaPanico.objects.create(tenant=tenant, servicio=servicio)
    atender_url = reverse("alerta-panico-atender", args=[alerta.pk])
    cerrar_url = reverse("alerta-panico-cerrar", args=[alerta.pk])

    assert api_client.post(cerrar_url).status_code == 400
    assert api_client.post(atender_url).status_code == 200
    assert api_client.post(atender_url).status_code == 400
    assert api_client.post(cerrar_url, {"notas_cierre": "Se verificó con el escolta."}).status_code == 200
    alerta.refresh_from_db()
    assert alerta.estado == AlertaPanico.Estado.CERRADA
    assert alerta.notas_cierre == "Se verificó con el escolta."


@pytest.mark.django_db
def test_no_permite_asignar_vehiculo_de_otro_tenant(api_client, tenant):
    otro_tenant = Tenant.objects.create(nombre="Otra empresa", subdominio="otra-empresa")
    vehiculo = Vehiculo.objects.create(tenant=otro_tenant, placa="XYZ123", tipo=Vehiculo.Tipo.CARRO)
    inicio = timezone.now()

    respuesta = api_client.post(
        reverse("servicio-escolta-list"),
        {
            "cliente_nombre": "Cliente",
            "origen": "Origen",
            "destino": "Destino",
            "vehiculo": vehiculo.pk,
            "programado_inicio": inicio.isoformat(),
            "programado_fin": (inicio + timedelta(hours=1)).isoformat(),
        },
    )

    assert respuesta.status_code == 400
    assert not ServicioEscolta.objects.filter(tenant=tenant).exists()


@pytest.mark.django_db
def test_no_permite_personal_de_otro_tenant(api_client, tenant):
    otro_tenant = Tenant.objects.create(nombre="Otra empresa", subdominio="otra-empresa")
    usuario = User.objects.create_user(username="escolta-externo", tenant=otro_tenant)
    inicio = timezone.now()

    respuesta = api_client.post(
        reverse("servicio-escolta-list"),
        {
            "cliente_nombre": "Cliente",
            "origen": "Origen",
            "destino": "Destino",
            "personal": [usuario.pk],
            "programado_inicio": inicio.isoformat(),
            "programado_fin": (inicio + timedelta(hours=1)).isoformat(),
        },
    )

    assert respuesta.status_code == 400
    assert not ServicioEscolta.objects.filter(tenant=tenant).exists()


@pytest.mark.django_db
def test_checkpoint_exige_servicio_en_curso_y_ubicacion_en_radio(api_client, tenant, servicio):
    checkpoint = CheckpointPlan.objects.create(
        tenant=tenant,
        servicio=servicio,
        orden=1,
        nombre="Peaje norte",
        lat=6.25,
        lng=-75.56,
        radio_tolerancia_metros=100,
    )
    registro_url = reverse("checkpoint-registro-list")
    payload = {"checkpoint": checkpoint.pk, "lat": 6.25, "lng": -75.56}

    assert api_client.post(registro_url, payload).status_code == 400

    servicio.estado = ServicioEscolta.Estado.EN_CURSO
    servicio.save(update_fields=["estado"])
    assert api_client.delete(
        reverse("checkpoint-plan-detail", args=[checkpoint.pk])
    ).status_code == 400
    respuesta_fuera_de_radio = api_client.post(
        registro_url, {"checkpoint": checkpoint.pk, "lat": 6.30, "lng": -75.56}
    )
    assert respuesta_fuera_de_radio.status_code == 400

    respuesta_en_checkpoint = api_client.post(registro_url, payload)
    assert respuesta_en_checkpoint.status_code == 201
    assert respuesta_en_checkpoint.data["a_tiempo"] is True


@pytest.mark.django_db
def test_no_expone_servicios_de_otro_tenant(api_client, tenant):
    otro_tenant = Tenant.objects.create(nombre="Otra empresa", subdominio="otra-empresa")
    inicio = timezone.now()
    servicio_ajeno = ServicioEscolta.objects.create(
        tenant=otro_tenant,
        cliente_nombre="Cliente ajeno",
        origen="Origen",
        destino="Destino",
        programado_inicio=inicio,
        programado_fin=inicio + timedelta(hours=1),
    )

    respuesta = api_client.get(reverse("servicio-escolta-list"))

    assert respuesta.status_code == 200
    assert all(item["id"] != servicio_ajeno.pk for item in respuesta.data)


@pytest.mark.django_db
def test_usuario_no_puede_elegir_otro_tenant_con_header(api_client, tenant):
    otro_tenant = Tenant.objects.create(nombre="Otra empresa", subdominio="otra-empresa")
    inicio = timezone.now()
    ServicioEscolta.objects.create(
        tenant=otro_tenant,
        cliente_nombre="Cliente ajeno",
        origen="Origen",
        destino="Destino",
        programado_inicio=inicio,
        programado_fin=inicio + timedelta(hours=1),
    )
    api_client.defaults["HTTP_X_TENANT_ID"] = str(otro_tenant.pk)

    respuesta = api_client.get(reverse("servicio-escolta-list"))

    assert respuesta.status_code == 403
