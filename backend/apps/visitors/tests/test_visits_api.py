"""
Pruebas del flujo núcleo: crear visita -> autorizar -> check-in -> check-out.
Sigue el mismo patrón de fixtures que apps.tickets.tests (tenant + usuario
autenticado vía conftest compartido).
"""

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.tenants.models import Tenant
from apps.visitors.models import Host, Sede, Visit, Visitor


@pytest.mark.django_db
def test_flujo_check_in_check_out(tenant, admin_user):
    client = APIClient()
    client.force_authenticate(admin_user)
    client.defaults["HTTP_X_TENANT_ID"] = str(tenant.pk)

    sede = Sede.objects.create(tenant=tenant, nombre="Torre Norte")
    host = Host.objects.create(
        tenant=tenant, sede=sede, nombre_completo="Ana Ríos", email="ana@example.com"
    )
    visitante = Visitor.objects.create(
        tenant=tenant,
        documento_numero="123456789",
        nombre_completo="Carlos Pérez",
        empresa="ACME S.A.S",
    )
    visita = Visit.objects.create(
        tenant=tenant,
        sede=sede,
        visitante=visitante,
        anfitrion=host,
        hora_autorizada_desde=timezone.now(),
        hora_autorizada_hasta=timezone.now() + timezone.timedelta(hours=2),
    )

    resp = client.post(f"/api/visitors/visitas/{visita.id}/autorizar/")
    assert resp.status_code == 200
    assert resp.data["estado"] == "autorizada"

    resp = client.post(f"/api/visitors/visitas/{visita.id}/check_in/")
    assert resp.status_code == 200
    assert resp.data["estado"] == "en_curso"
    assert resp.data["check_in_at"] is not None

    resp = client.post(f"/api/visitors/visitas/{visita.id}/check_out/")
    assert resp.status_code == 200
    assert resp.data["estado"] == "finalizada"
    assert resp.data["check_out_at"] is not None


@pytest.mark.django_db
def test_documento_unico_por_tenant(tenant):
    Visitor.objects.create(
        tenant=tenant, documento_numero="1", nombre_completo="Persona A"
    )
    with pytest.raises(Exception):
        Visitor.objects.create(
            tenant=tenant, documento_numero="1", nombre_completo="Persona B (duplicado)"
        )


@pytest.mark.django_db
def test_no_se_puede_asociar_visitante_de_otro_tenant(tenant, admin_user):
    otro_tenant = Tenant.objects.create(
        nombre="Otra empresa",
        subdominio="otra-empresa",
    )
    sede = Sede.objects.create(tenant=tenant, nombre="Sede propia")
    visitante_ajeno = Visitor.objects.create(
        tenant=otro_tenant,
        documento_numero="DOC-EXT-1",
        nombre_completo="Visitante ajeno",
    )
    client = APIClient()
    client.force_authenticate(admin_user)
    client.defaults["HTTP_X_TENANT_ID"] = str(tenant.pk)

    response = client.post(
        "/api/visitors/visitas/",
        {
            "sede": sede.pk,
            "visitante": visitante_ajeno.pk,
            "hora_autorizada_desde": timezone.now().isoformat(),
            "hora_autorizada_hasta": (timezone.now() + timezone.timedelta(hours=1)).isoformat(),
        },
        format="json",
    )

    assert response.status_code == 400
    assert not Visit.objects.filter(tenant=tenant).exists()


@pytest.mark.django_db
def test_usuario_recepcionista_solo_consulta_sedes_asignadas(tenant):
    recepcionista = User.objects.create_user(
        username="recepcion",
        password="password",
        tenant=tenant,
        rol=User.Rol.RECEPCIONISTA,
    )
    sede_asignada = Sede.objects.create(tenant=tenant, nombre="Sede asignada")
    Sede.objects.create(tenant=tenant, nombre="Sede no asignada")
    recepcionista.sedes.add(sede_asignada)
    client = APIClient()
    client.force_authenticate(recepcionista)
    client.defaults["HTTP_X_TENANT_ID"] = str(tenant.pk)

    sedes_response = client.get("/api/visitors/sedes/")
    riesgo_response = client.get("/api/risk/evaluaciones/")

    assert sedes_response.status_code == 200
    assert [sede["id"] for sede in sedes_response.data] == [sede_asignada.pk]
    assert riesgo_response.status_code == 403
