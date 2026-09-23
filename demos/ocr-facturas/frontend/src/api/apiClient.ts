import axios, { type AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type { ApiError } from '../types/api';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add JWT token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    // Handle 401 Unauthorized - clear token and redirect to login
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('username');
      // Only redirect if not already on login page
      if (!window.location.pathname.includes('/login')) {
        window.location.href = '/login';
      }
      return Promise.reject({
        detail: 'Sesión expirada. Inicie sesión nuevamente.',
        error_code: 'UNAUTHORIZED',
      });
    }

    const apiError: ApiError = {
      detail: 'Error de conexión. Intente nuevamente.',
      error_code: 'NETWORK_ERROR',
      correlation_id: undefined,
    };

    if (error.response) {
      const status = error.response.status;
      const data = error.response.data as ApiError | undefined;

      if (data && typeof data === 'object' && 'detail' in data) {
        apiError.detail = data.detail;
        apiError.error_code = data.error_code;
        apiError.correlation_id = data.correlation_id;
      } else if (status === 404) {
        apiError.detail = 'Recurso no encontrado.';
        apiError.error_code = 'NOT_FOUND';
      } else if (status === 400) {
        apiError.detail = (data as ApiError | undefined)?.detail || 'Solicitud inválida.';
        apiError.error_code = 'BAD_REQUEST';
      } else if (status === 409) {
        apiError.detail =
          (data as ApiError | undefined)?.detail || 'Conflicto con el estado actual.';
        apiError.error_code = 'CONFLICT';
      } else if (status === 503) {
        apiError.detail =
          (data as ApiError | undefined)?.detail || 'Servicio no disponible. Intente más tarde.';
        apiError.error_code = 'SERVICE_UNAVAILABLE';
      } else {
        apiError.detail = (data as ApiError | undefined)?.detail || 'Error del servidor.';
        apiError.error_code = 'SERVER_ERROR';
      }
    } else if (error.code === 'ECONNABORTED') {
      apiError.detail = 'La solicitud tardó demasiado. Intente nuevamente.';
      apiError.error_code = 'TIMEOUT';
    }

    return Promise.reject(apiError);
  },
);

export default apiClient;
