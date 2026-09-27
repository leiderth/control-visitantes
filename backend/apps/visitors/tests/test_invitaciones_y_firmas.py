import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.visitors.models import DocumentoLegal, Host, Invitacion, Sede, Visit, Visitor


@pytest.mark.django_db
def test_confirmar_invitacion_publica_sin_login(tenant):
    sede = Sede.objects.create(tenant=tenant, nombre="Torre Norte")
    host = Host.objects.create(tenant=tenant, sede=sede, nombre_completo="Ana Ríos", email="ana@example.com")
    invitacion = Invitacion.objects.create(
        tenant=tenant,
        sede=sede,
        anfitrion=host,
        visitante_nombre="Carlos Pérez",
        valida_desde=timezone.now(),
        valida_hasta=timezone.now() + timezone.timedelta(days=1),
    )

    client = APIClient()  # sin force_authenticate: simula al visitante externo
    resp = client.post(f"/api/visitors/invitaciones-publicas/{invitacion.token}/confirmar/")

    assert resp.status_code == 200
    assert resp.data["estado"] == "confirmada"


@pytest.mark.django_db
def test_check_in_bloqueado_si_falta_firma_obligatoria(tenant, admin_user):
    sede = Sede.objects.create(tenant=tenant, nombre="Torre Norte")
    visitante = Visitor.objects.create(
        tenant=tenant, documento_numero="1", nombre_completo="Contratista X", categoria="contratista"
    )
    DocumentoLegal.objects.create(
        tenant=tenant, nombre="Política de seguridad", contenido="...", obligatorio_para=["contratista"]
    )
    visita = Visit.objects.create(
        tenant=tenant,
        sede=sede,
        visitante=visitante,
        estado=Visit.Estado.AUTORIZADA,
        hora_autorizada_desde=timezone.now(),
        hora_autorizada_hasta=timezone.now() + timezone.timedelta(hours=2),
    )

    client = APIClient()
    client.force_authenticate(admin_user)
    client.defaults["HTTP_X_TENANT_ID"] = str(tenant.pk)
    resp = client.post(f"/api/visitors/visitas/{visita.id}/check_in/")

    assert resp.status_code == 400
    assert "Política de seguridad" in resp.data["documentos_pendientes"]
