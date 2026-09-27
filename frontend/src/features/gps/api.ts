import { apiClient } from '@/lib/api';

export interface Vehiculo {
  id: number;
  placa: string;
  tipo: 'moto' | 'carro' | 'a_pie';
  activo: boolean;
}

export interface UltimaPosicion {
  vehiculo: Vehiculo;
  lat: number;
  lng: number;
  capturado_en: string;
}

export const gpsApi = {
  listVehiculos: () => apiClient.get<Vehiculo[]>('/gps/vehiculos/'),
  listPosiciones: (dispositivoId: number) =>
    apiClient.get(`/gps/posiciones/?dispositivo=${dispositivoId}`),
  listGeocercaEventos: () => apiClient.get('/gps/geocerca-eventos/'),
};

// TODO (Fase 6): esta pantalla hoy no dibuja un mapa real — se integra
// Mapbox/Google Maps aquí cuando exista la API key del cliente; el layout
// ya deja el contenedor `#mapa` listo para inicializar la librería.
