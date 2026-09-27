import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.tenants.models import Tenant


@pytest.mark.django_db
def test_onboarding_creates_tenant_admin_modules_and_tokens():
    response = APIClient().post(
        reverse("tenant-onboarding"),
        {
            "company_name": "Seguridad Horizonte",
            "tenant_slug": "seguridad-horizonte",
            "first_name": "Ana",
            "last_name": "García",
            "email": "ana@example.com",
            "username": "ana-admin",
            "password": "Vigilancia-Segura-2026!",
        },
        format="json",
    )

    assert response.status_code == 201
    tenant = Tenant.objects.get(subdominio="seguridad-horizonte")
    user = User.objects.get(username="ana-admin")
    assert user.tenant == tenant
    assert user.rol == User.Rol.ADMIN_EMPRESA
    assert set(tenant.modulos.values_list("nombre_modulo", flat=True)) == {
        "visitors",
        "alarms",
        "gps",
        "escorts",
        "risk",
    }
    assert response.data["tenant"]["id"] == tenant.pk
    assert response.data["access"]
    assert response.data["refresh"]


@pytest.mark.django_db
def test_onboarding_rejects_duplicate_slug_without_partial_creation():
    Tenant.objects.create(nombre="Existente", subdominio="ya-existe")

    response = APIClient().post(
        reverse("tenant-onboarding"),
        {
            "company_name": "Nueva Empresa",
            "tenant_slug": "ya-existe",
            "first_name": "Ana",
            "last_name": "García",
            "email": "ana@example.com",
            "username": "ana-admin",
            "password": "Vigilancia-Segura-2026!",
        },
        format="json",
    )

    assert response.status_code == 400
    assert User.objects.filter(username="ana-admin").count() == 0
    assert Tenant.objects.count() == 1


@pytest.mark.django_db
def test_login_issues_tokens_only_for_the_selected_tenant(admin_user, tenant):
    admin_user.set_password("Vigilancia-Segura-2026!")
    admin_user.save()

    response = APIClient().post(
        reverse("auth-login"),
        {
            "tenant_slug": tenant.subdominio,
            "username": admin_user.username,
            "password": "Vigilancia-Segura-2026!",
        },
        format="json",
    )

    assert response.status_code == 200
    assert response.data["tenant"]["id"] == tenant.pk
    assert response.data["access"]

    refresh_response = APIClient().post(
        reverse("auth-refresh"),
        {"refresh": response.data["refresh"]},
        format="json",
    )
    assert refresh_response.status_code == 200
    assert refresh_response.data["access"]

    response_otro_tenant = APIClient().post(
        reverse("auth-login"),
        {
            "tenant_slug": "otra-empresa",
            "username": admin_user.username,
            "password": "Vigilancia-Segura-2026!",
        },
        format="json",
    )
    assert response_otro_tenant.status_code == 400


@pytest.mark.django_db
def test_authenticated_user_cannot_select_another_tenant(admin_user, tenant):
    other_tenant = Tenant.objects.create(nombre="Otra Empresa", subdominio="otra-empresa")
    client = APIClient()
    client.force_authenticate(admin_user)

    response = client.get(
        "/api/risk/evaluaciones/",
        HTTP_X_TENANT_ID=str(other_tenant.pk),
    )

    assert response.status_code == 403
