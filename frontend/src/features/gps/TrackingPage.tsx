import { useEffect, useState } from 'react';
import { getApiErrorMessage } from '@/lib/api';
import { gpsApi, Vehiculo } from './api';

/**
 * Vista de rastreo. Hasta que se conecte una librería de mapas real
 * (Mapbox/Google Maps, según la key que configure el cliente), se muestra
 * como lista de últimas posiciones — mismo dato, sin bloquear el resto del
 * flujo de geocercas mientras se resuelve esa integración.
 */
export function TrackingPage() {
  const [vehiculos, setVehiculos] = useState<Vehiculo[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    gpsApi.listVehiculos().then(({ data }) => {
      if (!Array.isArray(data)) throw new Error('La API de GPS no devolvió una lista válida.');
      setVehiculos(data);
    }).catch((loadError: unknown) => {
      setVehiculos([]);
      setError(getApiErrorMessage(loadError, 'No se pudieron cargar los vehículos.'));
    });
  }, []);

  return (
    <div className="p-6">
      <h1 className="mb-4 text-xl font-semibold">Rastreo de vehículos y guardias</h1>
      {error && <div className="notice notice-error" role="alert">{error}</div>}
      <div id="mapa" className="mb-4 flex h-64 items-center justify-center rounded border border-dashed text-sm text-zinc-400">
        Mapa (Mapbox/Google Maps) — pendiente de API key del cliente
      </div>
      <ul className="divide-y">
        {vehiculos.map((v) => (
          <li key={v.id} className="py-2">
            {v.placa || `Guardia #${v.id}`} — <span className="text-zinc-500">{v.tipo}</span>
          </li>
        ))}
        {!vehiculos.length && !error && <li className="py-3 text-sm">No hay vehículos registrados.</li>}
      </ul>
    </div>
  );
}
