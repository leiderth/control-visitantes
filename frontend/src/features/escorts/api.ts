import { apiClient } from '@/lib/api';
import type { AlertaPanico, ServicioEscolta } from './types';

export const escortsApi = {
  listServicios: (params?: { estado?: string }) =>
    apiClient.get<ServicioEscolta[]>('/escorts/servicios/', { params }),

  getServicio: (id: number) => apiClient.get<ServicioEscolta>(`/escorts/servicios/${id}/`),

  iniciar: (id: number) => apiClient.post<ServicioEscolta>(`/escorts/servicios/${id}/iniciar/`),

  finalizar: (id: number) => apiClient.post<ServicioEscolta>(`/escorts/servicios/${id}/finalizar/`),

  cancelar: (id: number, motivo?: string) =>
    apiClient.post<ServicioEscolta>(`/escorts/servicios/${id}/cancelar/`, { motivo }),

  dispararPanico: (id: number, lat?: number, lng?: number) =>
    apiClient.post<AlertaPanico>(`/escorts/servicios/${id}/panico/`, { lat, lng }),

  atenderAlerta: (id: number) => apiClient.post<AlertaPanico>(`/escorts/alertas-panico/${id}/atender/`),

  cerrarAlerta: (id: number, notas_cierre?: string) =>
    apiClient.post<AlertaPanico>(`/escorts/alertas-panico/${id}/cerrar/`, { notas_cierre }),
};

// TODO (Fase 6+): el botón de pánico en la app móvil del guardia debe poder
// dispararse offline y reintentar el POST cuando recupere señal — hoy este
// cliente asume conexión inmediata, igual que el resto del proyecto.
