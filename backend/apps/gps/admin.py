from django.contrib import admin

from .models import DispositivoGPS, Geocerca, GeocercaEvento, PosicionGPS, Vehiculo

admin.site.register(Vehiculo)
admin.site.register(DispositivoGPS)
admin.site.register(Geocerca)
admin.site.register(GeocercaEvento)
admin.site.register(PosicionGPS)
