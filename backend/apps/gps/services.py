"""
Lógica de geocercas: al registrar una PosicionGPS se evalúa contra todas
las geocercas activas del tenant y se genera un GeocercaEvento si hay
cambio de estado (entró/salió). Aislado de views.py por la misma razón
que apps.visitors.services: en Fase 6+ este cálculo se dispara desde un
consumer de Channels (cada posición llega por WebSocket, no por POST HTTP),
no desde un ViewSet.
"""

import math

from .models import Geocerca, GeocercaEvento, PosicionGPS


def _distancia_metros(lat1, lng1, lat2, lng2) -> float:
    """Distancia haversine — suficiente para radios de cientos de metros."""
    R = 6371000
    p1, p2 = math.radians(float(lat1)), math.radians(float(lat2))
    dp = math.radians(float(lat2) - float(lat1))
    dl = math.radians(float(lng2) - float(lng1))
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


def evaluar_geocercas(posicion: PosicionGPS) -> list[GeocercaEvento]:
    vehiculo = posicion.dispositivo.vehiculo
    eventos_creados = []

    for geocerca in Geocerca.objects.filter(tenant=posicion.tenant, activa=True):
        dentro_ahora = (
            _distancia_metros(posicion.lat, posicion.lng, geocerca.centro_lat, geocerca.centro_lng)
            <= geocerca.radio_metros
        )
        ultimo_evento = (
            GeocercaEvento.objects.filter(geocerca=geocerca, vehiculo=vehiculo).order_by("-ocurrido_en").first()
        )
        estaba_dentro = bool(ultimo_evento and ultimo_evento.tipo == GeocercaEvento.Tipo.ENTRADA)

        if dentro_ahora and not estaba_dentro:
            eventos_creados.append(
                GeocercaEvento.objects.create(
                    tenant=posicion.tenant, geocerca=geocerca, vehiculo=vehiculo, tipo=GeocercaEvento.Tipo.ENTRADA
                )
            )
        elif not dentro_ahora and estaba_dentro:
            eventos_creados.append(
                GeocercaEvento.objects.create(
                    tenant=posicion.tenant, geocerca=geocerca, vehiculo=vehiculo, tipo=GeocercaEvento.Tipo.SALIDA
                )
            )
    return eventos_creados
