import { useEffect, useState } from 'react';
import { getApiErrorMessage } from '@/lib/api';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { escortsApi } from './api';
import type { EstadoServicio, ServicioEscolta } from './types';

const ESTADO_COLOR: Record<EstadoServicio, 'green' | 'amber' | 'red' | 'gray'> = {
  programado: 'gray',
  en_curso: 'amber',
  finalizado: 'green',
  cancelado: 'red',
};

/**
 * Panel de escoltas: programación de servicios y su seguimiento en curso.
 * El botón de pánico queda siempre visible en un servicio "en_curso" — en
 * la app móvil real (Fase 6+) es un botón físico/gesto, aquí es el mismo
 * endpoint por HTTP mientras esa app no exista.
 */
export function EscortsPage() {
  const [servicios, setServicios] = useState<ServicioEscolta[]>([]);
  const [error, setError] = useState('');

  const cargar = async () => {
    try {
      const { data } = await escortsApi.listServicios();
      if (!Array.isArray(data)) throw new Error('La API de escoltas no devolvió una lista válida.');
      setServicios(data);
      setError('');
    } catch (loadError) {
      setServicios([]);
      setError(getApiErrorMessage(loadError, 'No se pudieron cargar los servicios de escolta.'));
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  return (
    <div className="p-6">
      <h1 className="mb-4 text-xl font-semibold">Escoltas</h1>
      {error && <div className="notice notice-error" role="alert">{error}</div>}
      <div className="divide-y rounded border">
        {servicios.map((s) => (
          <div key={s.id} className="flex items-center justify-between p-4">
            <div>
              <p className="font-medium">
                {s.cliente_nombre} — {s.origen} → {s.destino}
              </p>
              <p className="text-sm text-zinc-500">
                {new Date(s.programado_inicio).toLocaleString()}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Badge color={ESTADO_COLOR[s.estado]}>{s.estado}</Badge>
              {s.estado === 'programado' && (
                <Button size="sm" onClick={() => escortsApi.iniciar(s.id).then(cargar)}>
                  Iniciar
                </Button>
              )}
              {s.estado === 'en_curso' && (
                <>
                  <Button size="sm" onClick={() => escortsApi.finalizar(s.id).then(cargar)}>
                    Finalizar
                  </Button>
                  <Button
                    size="sm"
                    className="bg-red-600 hover:bg-red-700"
                    onClick={() => escortsApi.dispararPanico(s.id).then(cargar)}
                  >
                    Pánico
                  </Button>
                </>
              )}
            </div>
          </div>
        ))}
        {!servicios.length && !error && <p className="p-4 text-sm">No hay servicios de escolta registrados.</p>}
      </div>
    </div>
  );
}
