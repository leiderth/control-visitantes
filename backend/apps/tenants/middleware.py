"""
Resuelve `request.tenant` para que TenantScopedViewSetMixin (y cualquier
vista) pueda filtrar por tenant sin repetir la lógica de resolución.

En producción: por subdominio (`empresa.plataforma.com` → tenant con
subdominio="empresa"). En desarrollo/tests: por header `X-Tenant-Id`,
para no depender de DNS local.
"""

from django.http import HttpResponseForbidden

from .models import Tenant

PUBLIC_PATH_PREFIXES = (
    "/health/",
    "/api/auth/",
    "/api/onboarding/",
    "/api/visitors/invitaciones-publicas/",
)


class TenantResolutionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith(PUBLIC_PATH_PREFIXES):
            request.tenant = None
            return self.get_response(request)

        tenant = self._resolver(request)
        if tenant is None and not request.path.startswith("/admin/"):
            return HttpResponseForbidden("Tenant no identificado.")
        request.tenant = tenant
        return self.get_response(request)

    def _resolver(self, request):
        header_id = request.headers.get("X-Tenant-Id")
        if header_id:
            return Tenant.objects.filter(id=header_id, activo=True).first()

        host = request.get_host().split(":")[0]
        subdominio = host.split(".")[0]
        return Tenant.objects.filter(subdominio=subdominio, activo=True).first()
