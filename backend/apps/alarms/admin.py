from django.contrib import admin

from .models import AlarmEvent, DespachoLog, Sensor


@admin.register(Sensor)
class SensorAdmin(admin.ModelAdmin):
    list_display = ["nombre", "sede", "tipo", "activo"]
    list_filter = ["tipo", "activo", "sede"]


@admin.register(AlarmEvent)
class AlarmEventAdmin(admin.ModelAdmin):
    list_display = ["sensor", "severidad", "estado", "disparado_en"]
    list_filter = ["severidad", "estado"]


@admin.register(DespachoLog)
class DespachoLogAdmin(admin.ModelAdmin):
    list_display = ["evento", "operador", "asignado_en"]
