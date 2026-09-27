from rest_framework.permissions import IsAuthenticated

from .models import User

ALL_VIEW_ACTIONS = (
    "list",
    "retrieve",
    "create",
    "update",
    "partial_update",
    "destroy",
)
READ_ACTIONS = ("list", "retrieve")

ADMIN_SUPERVISOR = (User.Rol.ADMIN_EMPRESA, User.Rol.SUPERVISOR)
CENTRAL_OPERATIONS = (*ADMIN_SUPERVISOR, User.Rol.OPERADOR_CENTRAL)
ADMIN_SUPERVISOR_ACCESS = {
    User.Rol.ADMIN_EMPRESA: ALL_VIEW_ACTIONS,
    User.Rol.SUPERVISOR: ALL_VIEW_ACTIONS,
}
SITE_READ_ACCESS = {
    **{role: READ_ACTIONS for role in (User.Rol.RECEPCIONISTA, User.Rol.GUARDIA, User.Rol.OPERADOR_CENTRAL)},
}


class IsTenantMember(IsAuthenticated):
    def has_permission(self, request, view):
        if not super().has_permission(request, view) or request.tenant is None:
            return False
        if request.user.rol == User.Rol.SUPER_ADMIN:
            return True
        if request.user.tenant_id != request.tenant.pk:
            return False

        role_permissions = getattr(view, "role_permissions", None)
        if role_permissions is None:
            allowed_actions = ALL_VIEW_ACTIONS if request.user.rol in ADMIN_SUPERVISOR else ()
        else:
            allowed_actions = role_permissions.get(request.user.rol, ())
        return getattr(view, "action", None) in allowed_actions
