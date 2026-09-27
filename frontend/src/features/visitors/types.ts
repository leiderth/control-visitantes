export type CategoriaVisitante =
  | 'normal'
  | 'contratista'
  | 'proveedor'
  | 'mensajeria'
  | 'vip'
  | 'temporal';

export type EstadoVisita =
  | 'pendiente'
  | 'autorizada'
  | 'en_curso'
  | 'finalizada'
  | 'excedida'
  | 'rechazada';

export interface Sede {
  id: number;
  nombre: string;
  direccion: string;
  activa: boolean;
}

export interface Visitante {
  id: number;
  documento_tipo: string;
  documento_numero: string;
  nombre_completo: string;
  empresa: string;
  categoria: CategoriaVisitante;
  foto?: string | null;
  en_watchlist: boolean;
}

export interface Visita {
  id: number;
  codigo_qr: string;
  sede: number;
  visitante: number;
  visitante_detalle: Visitante;
  anfitrion: number | null;
  estado: EstadoVisita;
  hora_autorizada_desde: string;
  hora_autorizada_hasta: string;
  check_in_at: string | null;
  check_out_at: string | null;
}
