import { apiClient } from '@/lib/api';
import type { AlarmEvent } from './types';

export const alarmsApi = {
  listEventos: (params?: { estado?: string }) =>
    apiClient.get<AlarmEvent[]>('/alarms/eventos/', { params }),

  atender: (id: number, comentario?: string) =>
    apiClient.post<AlarmEvent>(`/alarms/eventos/${id}/atender/`, { comentario }),

  cerrar: (id: number, notas_cierre?: string) =>
    apiClient.post<AlarmEvent>(`/alarms/eventos/${id}/cerrar/`, { notas_cierre }),

  marcarFalsaAlarma: (id: number) =>
    apiClient.post<AlarmEvent>(`/alarms/eventos/${id}/marcar_falsa_alarma/`),
};

// TODO (Fase 5): reemplazar el polling de MonitoringPage por una suscripción
// WebSocket a `alarmas:{tenant_id}` para que los eventos nuevos aparezcan
// sin recargar — el backend ya deja la marca de dónde se debe publicar
// (ver comentario en apps/alarms/views.py::AlarmEventViewSet).
