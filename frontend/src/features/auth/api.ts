import { apiClient } from '@/lib/api';

export interface AuthSession {
  access: string;
  refresh: string;
  user: {
    id: number;
    username: string;
    name: string;
    role: string;
  };
  tenant: {
    id: number;
    name: string;
    slug: string;
  };
}

export interface LoginPayload {
  tenant_slug: string;
  username: string;
  password: string;
}

export interface OnboardingPayload extends LoginPayload {
  company_name: string;
  first_name: string;
  last_name: string;
  email: string;
}

export const authApi = {
  login: (payload: LoginPayload) =>
    apiClient.post<AuthSession>('/auth/login/', payload),
  onboard: (payload: OnboardingPayload) =>
    apiClient.post<AuthSession>('/auth/onboarding/', payload),
};
