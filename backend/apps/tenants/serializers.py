from django.core.exceptions import FieldDoesNotExist
from django.db.models import Q
from rest_framework import serializers


class TenantScopedSerializer(serializers.ModelSerializer):
    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return fields

        user = getattr(request, "user", None)
        assigned_sites = getattr(user, "sedes", None)
        site_ids = (
            assigned_sites.values_list("pk", flat=True)
            if assigned_sites is not None and assigned_sites.exists()
            else None
        )
        for field in fields.values():
            relation = field.child_relation if isinstance(field, serializers.ManyRelatedField) else field
            if not isinstance(relation, serializers.PrimaryKeyRelatedField) or relation.queryset is None:
                continue
            related_model = relation.queryset.model
            try:
                related_model._meta.get_field("tenant")
            except FieldDoesNotExist:
                continue
            relation.queryset = relation.queryset.filter(tenant=tenant)
            if site_ids is not None:
                if related_model._meta.label_lower == "visitors.sede":
                    relation.queryset = relation.queryset.filter(pk__in=site_ids)
                elif related_model._meta.label_lower == "accounts.user":
                    relation.queryset = relation.queryset.filter(
                        Q(sedes__in=site_ids) | Q(sedes__isnull=True)
                    ).distinct()
                elif any(field.name == "sede" for field in related_model._meta.fields):
                    relation.queryset = relation.queryset.filter(sede__in=site_ids)
        return fields

    def validate(self, attrs):
        request = self.context.get("request")
        tenant = getattr(request, "tenant", None)
        if tenant is None:
            return attrs
        for field, value in attrs.items():
            values = value if isinstance(value, (list, tuple, set)) else (value,)
            for related_object in values:
                related_tenant_id = getattr(related_object, "tenant_id", tenant.pk)
                if related_tenant_id != tenant.pk:
                    raise serializers.ValidationError(
                        {field: "El registro relacionado debe pertenecer a la empresa activa."}
                    )
        return attrs
