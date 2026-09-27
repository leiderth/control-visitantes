import axios, { type AxiosRequestConfig } from 'axios';

declare module 'axios' {
  export interface AxiosRequestConfig {
    _retry?: boolean;
  }
}

export function getApiErrorMessage(error: unknown, fallback: string) {
  if (!axios.isAxiosError(error)) {
    if (error instanceof Error) {
      const status = error.message.match(/status code (\d{3})/i)?.[1];
      if (status === '401') return 'Inicia sesión para consultar los datos de seguridad.';
      if (status === '403') return 'El backend rechazó la consulta. Falta identificar el tenant de la empresa.';
      if (status && Number(status) >= 500) return 'El servidor tuvo un error. Comprueba que el backend esté activo.';
    }
    return error instanceof Error ? error.message : fallback;
  }

  const status = error.response?.status;
  if (status === 401) return 'Inicia sesión para consultar los datos de seguridad.';
  if (status === 403) return 'No se identificó la empresa. Inicia sesión con un tenant activo.';
  if (status && status >= 500) return 'El servidor tuvo un error. Comprueba que el backend esté activo.';
  if (typeof error.response?.data === 'string' && error.response.data.length < 200) {
    return error.response.data;
  }
  return fallback;
}

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
});

let refreshRequest: Promise<string> | null = null;

export function clearAuthSession() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
  localStorage.removeItem('tenant_id');
  localStorage.removeItem('tenant_name');
  localStorage.removeItem('tenant_slug');
  localStorage.removeItem('user_name');
  localStorage.removeItem('user_role');
}

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  const tenantId = localStorage.getItem('tenant_id');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  if (tenantId) config.headers['X-Tenant-Id'] = tenantId;
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: unknown) => {
    if (!axios.isAxiosError(error) || error.response?.status !== 401 || !error.config) {
      return Promise.reject(error);
    }

    const request: AxiosRequestConfig = error.config;
    if (request._retry || request.url?.includes('/auth/')) {
      return Promise.reject(error);
    }

    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      clearAuthSession();
      window.location.assign('/login');
      return Promise.reject(error);
    }

    request._retry = true;
    refreshRequest ??= axios
      .post<{ access: string; refresh?: string }>(
        `${apiClient.defaults.baseURL}/auth/refresh/`,
        { refresh: refreshToken },
      )
      .then(({ data }) => {
        localStorage.setItem('access_token', data.access);
        if (data.refresh) localStorage.setItem('refresh_token', data.refresh);
        return data.access;
      })
      .finally(() => {
        refreshRequest = null;
      });

    try {
      const accessToken = await refreshRequest;
      request.headers = request.headers ?? {};
      request.headers.Authorization = `Bearer ${accessToken}`;
      return await apiClient(request);
    } catch (refreshError) {
      clearAuthSession();
      window.location.assign('/login');
      return Promise.reject(refreshError);
    }
  },
);
