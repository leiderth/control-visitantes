import { useEffect, useState } from 'react';
import { getApiErrorMessage } from '@/lib/api';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { visitorsApi } from './api';
import type { Visita } from './types';

const ESTADO_COLOR: Record<string, 'green' | 'amber' | 'red' | 'gray'> = {
  pendiente: 'gray',
  autorizada: 'amber',
  en_curso: 'green',
  finalizada: 'gray',
  excedida: 'red',
  rechazada: 'red',
};

/**
 * Pantalla de recepción / modo kiosco: lista las visitas del día con
 * acciones rápidas de autorizar, check-in y check-out.
 */
export function VisitorsPage() {
  const [visitas, setVisitas] = useState<Visita[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const cargar = async () => {
    setLoading(true);
    try {
      const { data } = await visitorsApi.listVisitas();
      if (!Array.isArray(data)) throw new Error('La API de visitantes no devolvió una lista válida.');
      setVisitas(data);
      setError('');
    } catch (loadError) {
      setVisitas([]);
      setError(getApiErrorMessage(loadError, 'No se pudieron cargar las visitas.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargar();
  }, []);

  const ejecutar = async (accion: 'autorizar' | 'checkIn' | 'checkOut', id: number) => {
    await visitorsApi[accion](id);
    await cargar();
  };

  if (loading) return <p>Cargando visitas…</p>;

  return (
    <div className="space-y-3">
      <h1 className="text-xl font-semibold">Visitantes de hoy</h1>
      {error && <div className="notice notice-error" role="alert">{error}</div>}
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-muted-foreground">
            <th>Visitante</th>
            <th>Empresa</th>
            <th>Estado</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {visitas.map((v) => (
            <tr key={v.id} className="border-t">
              <td>
                {v.visitante_detalle.nombre_completo}
                {v.visitante_detalle.en_watchlist && (
                  <Badge color="red" className="ml-2">
                    En watchlist
                  </Badge>
                )}
              </td>
              <td>{v.visitante_detalle.empresa}</td>
              <td>
                <Badge color={ESTADO_COLOR[v.estado]}>{v.estado}</Badge>
              </td>
              <td className="space-x-2">
                {v.estado === 'pendiente' && (
                  <Button size="sm" onClick={() => ejecutar('autorizar', v.id)}>
                    Autorizar
                  </Button>
                )}
                {v.estado === 'autorizada' && (
                  <Button size="sm" onClick={() => ejecutar('checkIn', v.id)}>
                    Check-in
                  </Button>
                )}
                {v.estado === 'en_curso' && (
                  <Button size="sm" onClick={() => ejecutar('checkOut', v.id)}>
                    Check-out
                  </Button>
                )}
              </td>
            </tr>
          ))}
          {!visitas.length && !error && <tr><td colSpan={4} className="py-5 text-center">No hay visitas registradas.</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
