from django.contrib import admin

from .models import AccionCorrectiva, EvaluacionRiesgo, IncidenteRiesgo


class AccionCorrectivaInline(admin.TabularInline):
    model = AccionCorrectiva
    extra = 0


@admin.register(EvaluacionRiesgo)
class EvaluacionRiesgoAdmin(admin.ModelAdmin):
    list_display = ["vulnerabilidad", "cliente_nombre", "sede", "probabilidad", "impacto", "estado"]
    list_filter = ["estado", "probabilidad", "impacto"]
    search_fields = ["cliente_nombre", "vulnerabilidad"]


@admin.register(IncidenteRiesgo)
class IncidenteRiesgoAdmin(admin.ModelAdmin):
    list_display = ["titulo", "cliente_nombre", "severidad", "estado", "ocurrido_en"]
    list_filter = ["estado", "severidad"]
    search_fields = ["cliente_nombre", "titulo"]
    inlines = [AccionCorrectivaInline]


admin.site.register(AccionCorrectiva)
