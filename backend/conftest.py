"""
Fixtures compartidas por los tests de todos los módulos (visitors, alarms...).
Mantiene la misma convención que se venía usando: `tenant` y `admin_user`
listos para inyectar en cualquier test de API.
"""

import pytest

from apps.accounts.models import User
from apps.tenants.models import Tenant


@pytest.fixture
def tenant(db):
    return Tenant.objects.create(nombre="Vigilancia Total S.A.S", subdominio="vigilancia-total")


@pytest.fixture
def admin_user(db, tenant):
    return User.objects.create_user(
        username="admin",
        password="admin12345",
        tenant=tenant,
        rol=User.Rol.ADMIN_EMPRESA,
        is_staff=True,
    )
