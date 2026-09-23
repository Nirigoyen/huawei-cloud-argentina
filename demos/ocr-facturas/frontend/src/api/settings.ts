import apiClient from './apiClient';
import type {
  AppSettings,
  CredentialUpdate,
  ConnectionTestResult,
  ServiceName,
  DifyModelsResponse,
  DifyDefaultPromptResponse,
} from '../types/settings';
import type { ApiMessage } from '../types/api';

export const settingsApi = {
  /**
   * Get current credential status (masked values)
   */
  getCredentials: async (): Promise<AppSettings> => {
    const response = await apiClient.get<AppSettings>('/settings/');
    return response.data;
  },

  /**
   * Save/update credentials
   */
  saveCredentials: async (credentials: CredentialUpdate): Promise<ApiMessage> => {
    const response = await apiClient.put<ApiMessage>('/settings/', credentials);
    return response.data;
  },

  /**
   * Test connection to a specific service
   */
  testConnection: async (service: ServiceName): Promise<ConnectionTestResult> => {
    const response = await apiClient.post<ConnectionTestResult>('/settings/test-connection', {
      service,
    });
    return response.data;
  },

  /**
   * Apply current settings to the Dify workflow
   */
  applySettingsToWorkflow: async (): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post<{ success: boolean; message: string }>(
      '/settings/apply-workflow',
    );
    return response.data;
  },

  /**
   * Test the destination database connection
   */
  testDestinationDatabase: async (): Promise<{ success: boolean; message: string }> => {
    const response = await apiClient.post<{ success: boolean; message: string }>(
      '/data-forward/test',
    );
    return response.data;
  },

  /**
   * Fetch available Dify LLM models
   */
  fetchDifyModels: async (): Promise<DifyModelsResponse> => {
    const response = await apiClient.get<DifyModelsResponse>('/settings/dify-models');
    return response.data;
  },

  /**
   * Fetch the default LLM prompt from the Dify workflow
   */
  fetchDifyDefaultPrompt: async (): Promise<DifyDefaultPromptResponse> => {
    const response = await apiClient.get<DifyDefaultPromptResponse>(
      '/settings/dify-default-prompt',
    );
    return response.data;
  },
};
