from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.tenants.models import Tenant

from .models import User


class LoginSerializer(serializers.Serializer):
    tenant_slug = serializers.SlugField(max_length=50)
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            username=attrs["username"],
            password=attrs["password"],
        )
        tenant = Tenant.objects.filter(subdominio=attrs["tenant_slug"], activo=True).first()
        if user is None or tenant is None or user.tenant_id != tenant.pk:
            raise serializers.ValidationError(
                {"detail": "Usuario, contraseña o empresa inválidos."}
            )
        attrs["user"] = user
        attrs["tenant"] = tenant
        return attrs


class OnboardingSerializer(serializers.Serializer):
    company_name = serializers.CharField(max_length=150)
    tenant_slug = serializers.SlugField(max_length=50)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate_tenant_slug(self, value):
        if Tenant.objects.filter(subdominio=value).exists():
            raise serializers.ValidationError("Este identificador de empresa ya está en uso.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso.")
        return value

    def validate(self, attrs):
        user = User(
            username=attrs["username"],
            first_name=attrs["first_name"],
            last_name=attrs["last_name"],
            email=attrs["email"],
        )
        try:
            validate_password(attrs["password"], user=user)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": list(error.messages)}) from error
        return attrs
