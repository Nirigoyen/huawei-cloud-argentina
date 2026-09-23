import { create } from 'zustand';
import { authApi } from '../api/auth';
import type { LoginRequest } from '../types/auth';

interface AuthState {
  isAuthenticated: boolean;
  username: string | null;
  isLoading: boolean;
  error: string | null;
  login: (data: LoginRequest) => Promise<boolean>;
  logout: () => void;
  checkAuth: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated: !!localStorage.getItem('access_token'),
  username: localStorage.getItem('username'),
  isLoading: false,
  error: null,

  login: async (data: LoginRequest) => {
    set({ isLoading: true, error: null });
    try {
      const response = await authApi.login(data);
      localStorage.setItem('access_token', response.access_token);
      localStorage.setItem('username', response.username);
      set({ isAuthenticated: true, username: response.username, isLoading: false });
      return true;
    } catch (error: any) {
      const message = error.response?.data?.detail || error.detail || 'Error al iniciar sesión';
      set({ isLoading: false, error: message });
      return false;
    }
  },

  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    set({ isAuthenticated: false, username: null });
  },

  checkAuth: async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      set({ isAuthenticated: false });
      return;
    }
    try {
      await authApi.verify();
      set({ isAuthenticated: true });
    } catch {
      localStorage.removeItem('access_token');
      localStorage.removeItem('username');
      set({ isAuthenticated: false, username: null });
    }
  },
}));
