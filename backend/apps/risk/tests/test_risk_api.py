from datetime import date, datetime, timedelta, timezone

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.risk.models import AccionCorrectiva, EvaluacionRiesgo, IncidenteRiesgo
from apps.tenants.models import Tenant
from apps.visitors.models import Sede


@pytest.fixture
def api_client(admin_user, tenant):
    client = APIClient()
    client.force_authenticate(admin_user)
    client.defaults["HTTP_X_TENANT_ID"] = str(tenant.pk)
    return client


@pytest.fixture
def sede(tenant):
    return Sede.objects.create(tenant=tenant, nombre="Centro logístico")


@pytest.fixture
def incidente(tenant, sede, admin_user):
    return IncidenteRiesgo.objects.create(
        tenant=tenant,
        cliente_nombre="Cliente industrial",
        sede=sede,
        titulo="Acceso no autorizado",
        descripcion="Ingreso fuera de horario en zona restringida.",
        severidad=IncidenteRiesgo.Severidad.ALTA,
        ocurrido_en=datetime.now(timezone.utc),
        reportado_por=admin_user,
    )


@pytest.mark.django_db
def test_nivel_de_riesgo_se_calcula_desde_probabilidad_e_impacto(api_client, sede):
    respuesta = api_client.post(
        reverse("evaluacion-riesgo-list"),
        {
            "cliente_nombre": "Cliente industrial",
            "sede": sede.pk,
            "vulnerabilidad": "Perímetro sin cobertura nocturna",
            "probabilidad": 4,
            "impacto": 5,
            "plan_mitigacion": "Instalar detección perimetral y ajustar rondas.",
        },
    )

    assert respuesta.status_code == 201
    assert respuesta.data["puntaje"] == 20
    assert respuesta.data["nivel"] == "critico"


@pytest.mark.django_db
def test_se_rechazan_relaciones_de_otro_tenant(api_client, tenant):
    otro_tenant = Tenant.objects.create(nombre="Otra empresa", subdominio="otra-empresa")
    sede_ajena = Sede.objects.create(tenant=otro_tenant, nombre="Sede ajena")

    respuesta = api_client.post(
        reverse("evaluacion-riesgo-list"),
        {
            "cliente_nombre": "Cliente industrial",
            "sede": sede_ajena.pk,
            "vulnerabilidad": "Acceso abierto",
            "probabilidad": 3,
            "impacto": 3,
            "plan_mitigacion": "Controlar acceso.",
        },
    )

    assert respuesta.status_code == 400
    assert not EvaluacionRiesgo.objects.filter(tenant=tenant).exists()


@pytest.mark.django_db
def test_incidente_requiere_sede_compatible_con_evaluacion(api_client, tenant, sede):
    otra_sede = Sede.objects.create(tenant=tenant, nombre="Sede secundaria")
    evaluacion = EvaluacionRiesgo.objects.create(
        tenant=tenant,
        cliente_nombre="Cliente industrial",
        sede=sede,
        vulnerabilidad="Punto ciego",
        probabilidad=3,
        impacto=4,
        plan_mitigacion="Instalar cámara.",
    )

    respuesta = api_client.post(
        reverse("incidente-riesgo-list"),
        {
            "cliente_nombre": "Cliente industrial",
            "sede": otra_sede.pk,
            "evaluacion": evaluacion.pk,
            "titulo": "Intento de ingreso",
            "descripcion": "Se reportó intento de acceso.",
            "severidad": "media",
            "ocurrido_en": datetime.now(timezone.utc).isoformat(),
        },
    )

    assert respuesta.status_code == 400
    assert not IncidenteRiesgo.objects.filter(tenant=tenant).exists()


@pytest.mark.django_db
def test_flujo_incidente_exige_completar_acciones_antes_de_cerrar(api_client, incidente, tenant):
    accion = AccionCorrectiva.objects.create(
        tenant=tenant,
        incidente=incidente,
        titulo="Actualizar protocolo de acceso",
        fecha_limite=date.today() + timedelta(days=3),
    )
    iniciar_url = reverse("incidente-riesgo-iniciar-seguimiento", args=[incidente.pk])
    resolver_url = reverse("incidente-riesgo-resolver", args=[incidente.pk])
    cerrar_url = reverse("incidente-riesgo-cerrar", args=[incidente.pk])

    assert api_client.post(resolver_url).status_code == 400
    assert api_client.post(iniciar_url).status_code == 200
    assert api_client.post(iniciar_url).status_code == 400
    assert api_client.post(resolver_url).status_code == 200
    assert api_client.post(cerrar_url).status_code == 400

    iniciar_accion_url = reverse("accion-correctiva-iniciar", args=[accion.pk])
    completar_accion_url = reverse("accion-correctiva-completar", args=[accion.pk])
    assert api_client.post(iniciar_accion_url).status_code == 200
    assert api_client.post(completar_accion_url).status_code == 200
    assert api_client.post(cerrar_url).status_code == 200

    incidente.refresh_from_db()
    accion.refresh_from_db()
    assert incidente.estado == IncidenteRiesgo.Estado.CERRADO
    assert accion.estado == AccionCorrectiva.Estado.COMPLETADA
    assert accion.completada_en is not None


@pytest.mark.django_db
def test_api_no_expone_incidentes_de_otro_tenant(api_client):
    otro_tenant = Tenant.objects.create(nombre="Otra empresa", subdominio="otra-empresa")
    incidente_ajeno = IncidenteRiesgo.objects.create(
        tenant=otro_tenant,
        cliente_nombre="Cliente ajeno",
        titulo="Incidente privado",
        descripcion="No debe ser visible.",
        severidad=IncidenteRiesgo.Severidad.CRITICA,
        ocurrido_en=datetime.now(timezone.utc),
    )

    respuesta = api_client.get(reverse("incidente-riesgo-list"))

    assert respuesta.status_code == 200
    assert all(item["id"] != incidente_ajeno.pk for item in respuesta.data)
