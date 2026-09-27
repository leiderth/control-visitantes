from django.contrib import admin

from .models import AlertaPanico, CheckpointPlan, CheckpointRegistro, ServicioEscolta


class CheckpointPlanInline(admin.TabularInline):
    model = CheckpointPlan
    extra = 0


@admin.register(ServicioEscolta)
class ServicioEscoltaAdmin(admin.ModelAdmin):
    list_display = ["cliente_nombre", "origen", "destino", "estado", "programado_inicio"]
    list_filter = ["estado"]
    inlines = [CheckpointPlanInline]


admin.site.register(CheckpointPlan)
admin.site.register(CheckpointRegistro)
admin.site.register(AlertaPanico)
