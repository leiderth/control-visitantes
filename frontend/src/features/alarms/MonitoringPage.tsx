import { useEffect, useState } from 'react';
import { getApiErrorMessage } from '@/lib/api';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { alarmsApi } from './api';
import type { AlarmEvent } from './types';

const SEVERIDAD_COLOR: Record<string, 'green' | 'amber' | 'red'> = {
  baja: 'green',
  media: 'amber',
  alta: 'red',
  critica: 'red',
};

/**
 * Pantalla de sala de monitoreo — pensada para pantalla grande, tema oscuro,
 * refresco periódico (polling cada 5s hasta que exista el canal WebSocket
 * de Fase 5). Cada tarjeta es un evento; las acciones de despacho quedan a
 * un clic para minimizar el tiempo de respuesta del operador.
 */
export function MonitoringPage() {
  const [eventos, setEventos] = useState<AlarmEvent[]>([]);
  const [error, setError] = useState('');

  const cargar = async () => {
    try {
      const { data } = await alarmsApi.listEventos();
      if (!Array.isArray(data)) {
        throw new Error('La API de alarmas no devolvió una lista válida.');
      }
      setEventos(data);
      setError('');
    } catch (loadError) {
      setEventos([]);
      setError(getApiErrorMessage(loadError, 'No se pudieron cargar las alarmas.'));
    }
  };

  useEffect(() => {
    cargar();
    const intervalo = setInterval(cargar, 5000);
    return () => clearInterval(intervalo);
  }, []);

  return (
    <div className="min-h-screen bg-zinc-950 p-6 text-zinc-100">
      <h1 className="mb-4 text-2xl font-semibold">Central de monitoreo</h1>
      {error && <div className="notice notice-error" role="alert">{error}</div>}
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
        {eventos.map((ev) => (
          <div key={ev.id} className="rounded-lg border border-zinc-800 bg-zinc-900 p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="font-medium">{ev.sensor_detalle.nombre}</p>
                <p className="text-sm text-zinc-400">{ev.sensor_detalle.tipo}</p>
              </div>
              <Badge color={SEVERIDAD_COLOR[ev.severidad]}>{ev.severidad}</Badge>
            </div>
            <p className="mt-2 text-xs text-zinc-500">
              {new Date(ev.disparado_en).toLocaleTimeString()}
            </p>
            <div className="mt-3 flex gap-2">
              {ev.estado === 'activa' && (
                <Button size="sm" onClick={() => alarmsApi.atender(ev.id).then(cargar)}>
                  Atender
                </Button>
              )}
              {ev.estado === 'en_atencion' && (
                <Button size="sm" onClick={() => alarmsApi.cerrar(ev.id).then(cargar)}>
                  Cerrar
                </Button>
              )}
              {ev.estado === 'activa' && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => alarmsApi.marcarFalsaAlarma(ev.id).then(cargar)}
                >
                  Falsa alarma
                </Button>
              )}
            </div>
          </div>
        ))}
        {!eventos.length && !error && <p>No hay alarmas registradas.</p>}
      </div>
    </div>
  );
}
