import { create } from 'zustand';
import { dashboardApi } from '../api/dashboard';
import type { DashboardStats } from '../types/dashboard';
import type { ApiError } from '../types/api';

interface DashboardState {
  stats: DashboardStats | null;
  loading: boolean;
  error: string | null;
  fetchStats: () => Promise<void>;
}

const defaultStats: DashboardStats = {
  total_invoices: 0,
  total_spending: 0,
  average_invoice_amount: 0,
  invoices_by_type: {},
  top_suppliers: [],
  monthly_trend: [],
  status_summary: {},
};

export const useDashboardStore = create<DashboardState>((set) => ({
  stats: null,
  loading: false,
  error: null,

  fetchStats: async () => {
    set({ loading: true, error: null });
    try {
      const data = await dashboardApi.stats();
      set({ stats: data, loading: false });
    } catch (err) {
      const apiErr = err as ApiError;
      set({ loading: false, error: apiErr.detail || 'Error al cargar estadísticas.' });
    }
  },
}));

export { defaultStats };
