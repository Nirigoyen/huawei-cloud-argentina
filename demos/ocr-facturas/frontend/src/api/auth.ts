import apiClient from './apiClient';
import type { LoginRequest, LoginResponse } from '../types/auth';

export const authApi = {
  login: async (data: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>('/auth/login', data);
    return response.data;
  },

  verify: async (): Promise<{ valid: boolean }> => {
    const response = await apiClient.post<{ valid: boolean }>('/auth/verify');
    return response.data;
  },
};
