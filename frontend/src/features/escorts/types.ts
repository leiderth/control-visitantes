export type EstadoServicio = 'programado' | 'en_curso' | 'finalizado' | 'cancelado';
export type EstadoAlertaPanico = 'activa' | 'atendida' | 'cerrada';

export interface CheckpointRegistro {
  id: number;
  checkpoint: number;
  lat: number;
  lng: number;
  registrado_en: string;
  a_tiempo: boolean;
}

export interface CheckpointPlan {
  id: number;
  servicio: number;
  orden: number;
  nombre: string;
  lat: number;
  lng: number;
  hora_estimada: string | null;
  radio_tolerancia_metros: number;
  registros: CheckpointRegistro[];
}

export interface AlertaPanico {
  id: number;
  servicio: number;
  lat: number | null;
  lng: number | null;
  disparado_en: string;
  estado: EstadoAlertaPanico;
  atendido_en: string | null;
  cerrado_en: string | null;
}

export interface ServicioEscolta {
  id: number;
  cliente_nombre: string;
  origen: string;
  destino: string;
  vehiculo: number | null;
  programado_inicio: string;
  programado_fin: string;
  iniciado_en: string | null;
  finalizado_en: string | null;
  estado: EstadoServicio;
  notas: string;
  checkpoints_plan?: CheckpointPlan[];
  alertas_panico?: AlertaPanico[];
}
