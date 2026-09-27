export type SeveridadAlarma = 'baja' | 'media' | 'alta' | 'critica';
export type EstadoAlarma = 'activa' | 'en_atencion' | 'cerrada' | 'falsa_alarma';

export interface Sensor {
  id: number;
  sede: number;
  nombre: string;
  tipo: 'puerta' | 'movimiento' | 'panico' | 'incendio' | 'perimetral';
  activo: boolean;
}

export interface AlarmEvent {
  id: number;
  sensor: number;
  sensor_detalle: Sensor;
  severidad: SeveridadAlarma;
  estado: EstadoAlarma;
  disparado_en: string;
  atendido_en: string | null;
  cerrado_en: string | null;
}
