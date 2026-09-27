from datetime import timedelta

import pytest
from django.utils import timezone

from apps.escorts.models import AlertaPanico, CheckpointPlan, CheckpointRegistro, ServicioEscolta
from apps.escorts.services import registrar_checkpoint


@pytest.fixture
def servicio(db, tenant):
    ahora = timezone.now()
    return ServicioEscolta.objects.create(
        tenant=tenant,
        cliente_nombre="Banco Andino",
        origen="Bodega central",
        destino="Sucursal El Poblado",
        programado_inicio=ahora,
        programado_fin=ahora + timedelta(hours=2),
    )


@pytest.mark.django_db
def test_flujo_de_estados_del_servicio(servicio):
    assert servicio.estado == ServicioEscolta.Estado.PROGRAMADO

    servicio.estado = ServicioEscolta.Estado.EN_CURSO
    servicio.iniciado_en = timezone.now()
    servicio.save()
    servicio.refresh_from_db()
    assert servicio.estado == ServicioEscolta.Estado.EN_CURSO

    servicio.estado = ServicioEscolta.Estado.FINALIZADO
    servicio.finalizado_en = timezone.now()
    servicio.save()
    servicio.refresh_from_db()
    assert servicio.estado == ServicioEscolta.Estado.FINALIZADO
    assert servicio.finalizado_en is not None


@pytest.mark.django_db
def test_checkpoint_a_tiempo_dentro_de_tolerancia(tenant, servicio):
    hora_estimada = timezone.now()
    checkpoint = CheckpointPlan.objects.create(
        tenant=tenant, servicio=servicio, orden=1, nombre="Peaje norte",
        lat=6.25, lng=-75.56, hora_estimada=hora_estimada,
    )
    servicio.estado = ServicioEscolta.Estado.EN_CURSO
    servicio.save(update_fields=["estado"])

    registro = registrar_checkpoint(
        checkpoint, lat=6.25, lng=-75.56, momento=hora_estimada + timedelta(minutes=5)
    )

    assert isinstance(registro, CheckpointRegistro)
    assert registro.a_tiempo is True


@pytest.mark.django_db
def test_checkpoint_tarde_fuera_de_tolerancia(tenant, servicio):
    hora_estimada = timezone.now()
    checkpoint = CheckpointPlan.objects.create(
        tenant=tenant, servicio=servicio, orden=1, nombre="Peaje norte",
        lat=6.25, lng=-75.56, hora_estimada=hora_estimada,
    )
    servicio.estado = ServicioEscolta.Estado.EN_CURSO
    servicio.save(update_fields=["estado"])

    registro = registrar_checkpoint(
        checkpoint, lat=6.25, lng=-75.56, momento=hora_estimada + timedelta(minutes=25)
    )

    assert registro.a_tiempo is False


@pytest.mark.django_db
def test_checkpoint_sin_hora_estimada_siempre_a_tiempo(tenant, servicio):
    checkpoint = CheckpointPlan.objects.create(
        tenant=tenant, servicio=servicio, orden=1, nombre="Punto libre", lat=6.25, lng=-75.56,
    )
    servicio.estado = ServicioEscolta.Estado.EN_CURSO
    servicio.save(update_fields=["estado"])

    registro = registrar_checkpoint(checkpoint, lat=6.25, lng=-75.56)

    assert registro.a_tiempo is True


@pytest.mark.django_db
def test_alerta_de_panico_queda_activa(tenant, servicio):
    alerta = AlertaPanico.objects.create(tenant=tenant, servicio=servicio, lat=6.25, lng=-75.56)

    assert alerta.estado == AlertaPanico.Estado.ACTIVA
    assert servicio.alertas_panico.count() == 1


@pytest.mark.django_db
def test_orden_de_checkpoint_es_unico_por_servicio(tenant, servicio):
    CheckpointPlan.objects.create(tenant=tenant, servicio=servicio, orden=1, nombre="A", lat=6.2, lng=-75.5)
    with pytest.raises(Exception):
        CheckpointPlan.objects.create(tenant=tenant, servicio=servicio, orden=1, nombre="B", lat=6.3, lng=-75.6)
