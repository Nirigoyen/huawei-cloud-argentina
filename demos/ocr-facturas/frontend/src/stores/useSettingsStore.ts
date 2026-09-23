import { create } from 'zustand';
import { settingsApi } from '../api/settings';
import type {
  AppSettings,
  CredentialUpdate,
  ConnectionTestState,
  ServiceName,
} from '../types/settings';
import type { ApiError } from '../types/api';

interface SettingsState {
  credentials: AppSettings | null;
  loading: boolean;
  error: string | null;
  saving: boolean;
  saveError: string | null;
  saveSuccess: boolean;
  connectionTests: Record<ServiceName, ConnectionTestState>;
  applyingWorkflow: boolean;
  applyWorkflowError: string | null;
  applyWorkflowSuccess: boolean;
  testingDb: boolean;
  testDbResult: { success: boolean; message: string } | null;
  fetchCredentials: () => Promise<void>;
  saveCredentials: (credentials: CredentialUpdate) => Promise<void>;
  testConnection: (service: ServiceName) => Promise<void>;
  applyWorkflow: () => Promise<void>;
  testDestinationDb: () => Promise<void>;
  clearSaveState: () => void;
  clearApplyWorkflowState: () => void;
  clearTestDbResult: () => void;
}

const defaultConnectionTests: Record<ServiceName, ConnectionTestState> = {
  huawei_iam: { status: 'idle', message: null, latency_ms: null },
  dify: { status: 'idle', message: null, latency_ms: null },
  maas: { status: 'idle', message: null, latency_ms: null },
};

export const useSettingsStore = create<SettingsState>((set) => ({
  credentials: null,
  loading: false,
  error: null,
  saving: false,
  saveError: null,
  saveSuccess: false,
  connectionTests: { ...defaultConnectionTests },
  applyingWorkflow: false,
  applyWorkflowError: null,
  applyWorkflowSuccess: false,
  testingDb: false,
  testDbResult: null,

  fetchCredentials: async () => {
    set({ loading: true, error: null });
    try {
      const data = await settingsApi.getCredentials();
      set({ credentials: data, loading: false });
    } catch (err) {
      const apiErr = err as ApiError;
      set({ loading: false, error: apiErr.detail || 'Error al cargar credenciales.' });
    }
  },

  saveCredentials: async (credentials) => {
    set({ saving: true, saveError: null, saveSuccess: false });
    try {
      await settingsApi.saveCredentials(credentials);
      set({ saving: false, saveSuccess: true });
      // Refresh credentials after save
      const data = await settingsApi.getCredentials();
      set({ credentials: data });
    } catch (err) {
      const apiErr = err as ApiError;
      set({ saving: false, saveError: apiErr.detail || 'Error al guardar credenciales.' });
    }
  },

  testConnection: async (service) => {
    set((state) => ({
      connectionTests: {
        ...state.connectionTests,
        [service]: { status: 'testing', message: null, latency_ms: null },
      },
    }));

    try {
      const result = await settingsApi.testConnection(service);
      set((state) => ({
        connectionTests: {
          ...state.connectionTests,
          [service]: {
            status: result.success ? 'success' : 'failure',
            message: result.message,
            latency_ms: result.latency_ms,
          },
        },
      }));
    } catch (err) {
      const apiErr = err as ApiError;
      set((state) => ({
        connectionTests: {
          ...state.connectionTests,
          [service]: {
            status: 'failure',
            message: apiErr.detail || 'Error al probar conexión.',
            latency_ms: null,
          },
        },
      }));
    }
  },

  clearSaveState: () => {
    set({ saveError: null, saveSuccess: false });
  },

  applyWorkflow: async () => {
    set({ applyingWorkflow: true, applyWorkflowError: null, applyWorkflowSuccess: false });
    try {
      const result = await settingsApi.applySettingsToWorkflow();
      if (result.success) {
        set({ applyingWorkflow: false, applyWorkflowSuccess: true });
      } else {
        set({ applyingWorkflow: false, applyWorkflowError: result.message });
      }
    } catch (err) {
      const apiErr = err as ApiError;
      set({
        applyingWorkflow: false,
        applyWorkflowError: apiErr.detail || 'Error al aplicar al workflow.',
      });
    }
  },

  clearApplyWorkflowState: () => {
    set({ applyWorkflowError: null, applyWorkflowSuccess: false });
  },

  testDestinationDb: async () => {
    set({ testingDb: true, testDbResult: null });
    try {
      const result = await settingsApi.testDestinationDatabase();
      set({ testingDb: false, testDbResult: result });
    } catch (err) {
      const apiErr = err as ApiError;
      set({
        testingDb: false,
        testDbResult: {
          success: false,
          message: apiErr.detail || 'Error al probar la base de datos destino.',
        },
      });
    }
  },

  clearTestDbResult: () => {
    set({ testDbResult: null });
  },
}));
