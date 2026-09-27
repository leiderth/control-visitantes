from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from apps.tenants.models import Tenant, TenantModule

from .models import User
from .serializers import LoginSerializer, OnboardingSerializer

DEFAULT_MODULES = ("visitors", "alarms", "gps", "escorts", "risk")


def session_payload(user, tenant):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
        "user": {
            "id": user.pk,
            "username": user.username,
            "name": user.get_full_name() or user.username,
            "role": user.rol,
        },
        "tenant": {
            "id": tenant.pk,
            "name": tenant.nombre,
            "slug": tenant.subdominio,
        },
    }


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "login"

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        return Response(
            session_payload(serializer.validated_data["user"], serializer.validated_data["tenant"])
        )


class OnboardingView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "onboarding"

    def post(self, request):
        serializer = OnboardingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        with transaction.atomic():
            tenant = Tenant.objects.create(
                nombre=data["company_name"],
                subdominio=data["tenant_slug"],
            )
            user = User.objects.create_user(
                username=data["username"],
                password=data["password"],
                email=data["email"],
                first_name=data["first_name"],
                last_name=data["last_name"],
                tenant=tenant,
                rol=User.Rol.ADMIN_EMPRESA,
            )
            TenantModule.objects.bulk_create(
                [TenantModule(tenant=tenant, nombre_modulo=name) for name in DEFAULT_MODULES]
            )
        return Response(session_payload(user, tenant), status=status.HTTP_201_CREATED)


class RefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = (ScopedRateThrottle,)
    throttle_scope = "auth_refresh"
    serializer_class = TokenRefreshSerializer
