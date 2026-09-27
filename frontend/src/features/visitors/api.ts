import { apiClient } from '@/lib/api';
import type { Sede, Visita, Visitante } from './types';

export const visitorsApi = {
  listSedes: () => apiClient.get<Sede[]>('/visitors/sedes/'),

  listVisitas: (params?: { sede?: number; estado?: string }) =>
    apiClient.get<Visita[]>('/visitors/visitas/', { params }),

  crearVisitante: (data: Partial<Visitante>) =>
    apiClient.post<Visitante>('/visitors/visitantes/', data),

  crearVisita: (data: Partial<Visita>) =>
    apiClient.post<Visita>('/visitors/visitas/', data),

  autorizar: (id: number) =>
    apiClient.post<Visita>(`/visitors/visitas/${id}/autorizar/`),

  checkIn: (id: number) =>
    apiClient.post<Visita>(`/visitors/visitas/${id}/check_in/`),

  checkOut: (id: number) =>
    apiClient.post<Visita>(`/visitors/visitas/${id}/check_out/`),
};

export const invitationsApi = {
  crear: (data: Record<string, unknown>) => apiClient.post('/visitors/invitaciones/', data),

  // Endpoint público (sin token de sesión) usado por la página que abre el
  // visitante desde el link/QR recibido por email o WhatsApp.
  confirmarPublica: (token: string) =>
    apiClient.post(`/visitors/invitaciones-publicas/${token}/confirmar/`),
};

export const gafeteApi = {
  obtener: (visitaId: number) =>
    apiClient.get<{ gafete_url: string }>(`/visitors/visitas/${visitaId}/gafete/`),
};
