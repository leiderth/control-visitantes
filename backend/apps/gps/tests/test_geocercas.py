import pytest
from django.utils import timezone

from apps.gps.models import DispositivoGPS, Geocerca, GeocercaEvento, PosicionGPS, Vehiculo
from apps.gps.services import evaluar_geocercas
from apps.visitors.models import Sede


@pytest.mark.django_db
def test_genera_evento_de_entrada_al_cruzar_geocerca(tenant):
    sede = Sede.objects.create(tenant=tenant, nombre="Torre Norte")
    geocerca = Geocerca.objects.create(
        tenant=tenant, sede=sede, nombre="Perímetro sede", centro_lat=6.244, centro_lng=-75.581, radio_metros=200
    )
    vehiculo = Vehiculo.objects.create(tenant=tenant, placa="ABC123", tipo="moto")
    dispositivo = DispositivoGPS.objects.create(tenant=tenant, vehiculo=vehiculo, identificador_externo="dev-1")

    # Posición prácticamente en el centro de la geocerca → debe generar "entrada"
    posicion = PosicionGPS.objects.create(
        tenant=tenant, dispositivo=dispositivo, lat=6.2440, lng=-75.5810, capturado_en=timezone.now()
    )
    eventos = evaluar_geocercas(posicion)

    assert len(eventos) == 1
    assert eventos[0].tipo == GeocercaEvento.Tipo.ENTRADA


@pytest.mark.django_db
def test_no_duplica_evento_si_sigue_dentro(tenant):
    sede = Sede.objects.create(tenant=tenant, nombre="Torre Norte")
    geocerca = Geocerca.objects.create(
        tenant=tenant, sede=sede, nombre="Perímetro sede", centro_lat=6.244, centro_lng=-75.581, radio_metros=200
    )
    vehiculo = Vehiculo.objects.create(tenant=tenant, placa="ABC123", tipo="moto")
    dispositivo = DispositivoGPS.objects.create(tenant=tenant, vehiculo=vehiculo, identificador_externo="dev-1")

    for _ in range(2):
        posicion = PosicionGPS.objects.create(
            tenant=tenant, dispositivo=dispositivo, lat=6.2440, lng=-75.5810, capturado_en=timezone.now()
        )
        eventos = evaluar_geocercas(posicion)

    # La segunda posición (sigue dentro) no debe generar un nuevo evento
    assert len(eventos) == 0
