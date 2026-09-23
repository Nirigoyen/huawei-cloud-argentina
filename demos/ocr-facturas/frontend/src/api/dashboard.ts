import apiClient from './apiClient';
import type { DashboardStats } from '../types/dashboard';

export const dashboardApi = {
  /**
   * Get dashboard statistics
   */
  stats: async (): Promise<DashboardStats> => {
    const response = await apiClient.get<DashboardStats>('/dashboard/stats');
    return response.data;
  },
};
