import { apiClient } from '@/lib/api';
import type { AccionCorrectiva, EvaluacionRiesgo, IncidenteRiesgo, Sede } from './types';

export const riskApi = {
  listEvaluaciones: () => apiClient.get<EvaluacionRiesgo[]>('/risk/evaluaciones/'),
  createEvaluacion: (payload: Record<string, unknown>) =>
    apiClient.post<EvaluacionRiesgo>('/risk/evaluaciones/', payload),
  listIncidentes: () => apiClient.get<IncidenteRiesgo[]>('/risk/incidentes/'),
  createIncidente: (payload: Record<string, unknown>) =>
    apiClient.post<IncidenteRiesgo>('/risk/incidentes/', payload),
  iniciarSeguimiento: (id: number) =>
    apiClient.post<IncidenteRiesgo>(`/risk/incidentes/${id}/iniciar_seguimiento/`),
  resolverIncidente: (id: number) =>
    apiClient.post<IncidenteRiesgo>(`/risk/incidentes/${id}/resolver/`),
  cerrarIncidente: (id: number) =>
    apiClient.post<IncidenteRiesgo>(`/risk/incidentes/${id}/cerrar/`),
  createAccion: (payload: Record<string, unknown>) =>
    apiClient.post<AccionCorrectiva>('/risk/acciones/', payload),
  iniciarAccion: (id: number) =>
    apiClient.post<AccionCorrectiva>(`/risk/acciones/${id}/iniciar/`),
  completarAccion: (id: number) =>
    apiClient.post<AccionCorrectiva>(`/risk/acciones/${id}/completar/`),
  listSedes: () => apiClient.get<Sede[]>('/visitors/sedes/'),
};
