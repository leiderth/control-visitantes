export type NivelRiesgo = 'bajo' | 'medio' | 'alto' | 'critico';
export type EstadoEvaluacion = 'identificado' | 'en_tratamiento' | 'mitigado' | 'aceptado';
export type SeveridadIncidente = 'baja' | 'media' | 'alta' | 'critica';
export type EstadoIncidente = 'abierto' | 'en_seguimiento' | 'resuelto' | 'cerrado';
export type EstadoAccion = 'pendiente' | 'en_progreso' | 'completada';

export interface Sede {
  id: number;
  nombre: string;
  direccion: string;
}

export interface EvaluacionRiesgo {
  id: number;
  cliente_nombre: string;
  sede: number | null;
  vulnerabilidad: string;
  descripcion: string;
  probabilidad: number;
  impacto: number;
  puntaje: number;
  nivel: NivelRiesgo;
  plan_mitigacion: string;
  responsable: number | null;
  estado: EstadoEvaluacion;
  estado_display: string;
  revisado_en: string | null;
  creado_en: string;
  actualizado_en: string;
}

export interface AccionCorrectiva {
  id: number;
  incidente: number;
  titulo: string;
  descripcion: string;
  responsable: number | null;
  responsable_nombre: string | null;
  fecha_limite: string | null;
  estado: EstadoAccion;
  estado_display: string;
  completada_en: string | null;
  creada_en: string;
}

export interface IncidenteRiesgo {
  id: number;
  cliente_nombre: string;
  sede: number | null;
  sede_nombre: string | null;
  evaluacion: number | null;
  titulo: string;
  descripcion: string;
  severidad: SeveridadIncidente;
  estado: EstadoIncidente;
  estado_display: string;
  ocurrido_en: string;
  reportado_por: number | null;
  reportado_por_nombre: string | null;
  acciones: AccionCorrectiva[];
  creado_en: string;
  actualizado_en: string;
}
