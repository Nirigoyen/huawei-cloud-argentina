import { create } from 'zustand';
import { invoiceApi } from '../api/invoices';
import type {
  InvoiceSummary,
  InvoiceDetail,
  InvoiceListParams,
  InvoiceStatus,
  InvoiceType,
  InvoiceUploadResponse,
} from '../types/invoice';
import type { PaginatedResponse, ApiError } from '../types/api';

interface InvoiceState {
  // List state
  invoices: InvoiceSummary[];
  total: number;
  page: number;
  pageSize: number;
  filters: {
    status: InvoiceStatus | '';
    invoice_type: InvoiceType | '';
    sort_by: string;
    sort_order: 'asc' | 'desc';
  };
  loading: boolean;
  error: string | null;

  // Detail state
  currentInvoice: InvoiceDetail | null;
  detailLoading: boolean;
  detailError: string | null;

  // Upload state
  uploading: boolean;
  uploadError: string | null;
  uploadResult: { invoice_id: string; status: InvoiceStatus } | null;

  // Actions
  fetchInvoices: (params?: Partial<InvoiceListParams>) => Promise<void>;
  fetchInvoiceDetail: (id: string) => Promise<void>;
  uploadInvoice: (file: File) => Promise<InvoiceUploadResponse>;
  retryInvoice: (id: string) => Promise<void>;
  setFilters: (filters: Partial<InvoiceState['filters']>) => void;
  setPage: (page: number) => void;
  clearUploadState: () => void;
  clearCurrentInvoice: () => void;
}

export const useInvoiceStore = create<InvoiceState>((set, get) => ({
  invoices: [],
  total: 0,
  page: 1,
  pageSize: 20,
  filters: {
    status: '',
    invoice_type: '',
    sort_by: 'created_at',
    sort_order: 'desc',
  },
  loading: false,
  error: null,
  currentInvoice: null,
  detailLoading: false,
  detailError: null,
  uploading: false,
  uploadError: null,
  uploadResult: null,

  fetchInvoices: async (params) => {
    set({ loading: true, error: null });
    try {
      const state = get();
      const requestParams: InvoiceListParams = {
        page: params?.page ?? state.page,
        page_size: params?.page_size ?? state.pageSize,
        status: params?.status ?? state.filters.status,
        invoice_type: params?.invoice_type ?? state.filters.invoice_type,
        sort_by: params?.sort_by ?? state.filters.sort_by,
        sort_order: params?.sort_order ?? state.filters.sort_order,
      };

      const data: PaginatedResponse<InvoiceSummary> = await invoiceApi.list(requestParams);
      set({
        invoices: data.items,
        total: data.total,
        page: data.page,
        pageSize: data.page_size,
        loading: false,
      });
    } catch (err) {
      const apiErr = err as ApiError;
      set({ loading: false, error: apiErr.detail || 'Error al cargar facturas.' });
    }
  },

  fetchInvoiceDetail: async (id) => {
    set({ detailLoading: true, detailError: null, currentInvoice: null });
    try {
      const data = await invoiceApi.detail(id);
      set({ currentInvoice: data, detailLoading: false });
    } catch (err) {
      const apiErr = err as ApiError;
      set({ detailLoading: false, detailError: apiErr.detail || 'Error al cargar detalle.' });
    }
  },

  uploadInvoice: async (file) => {
    set({ uploading: true, uploadError: null, uploadResult: null });
    try {
      const data = await invoiceApi.upload(file);
      set({ uploading: false, uploadResult: data });
      return data;
    } catch (err) {
      const apiErr = err as ApiError;
      set({ uploading: false, uploadError: apiErr.detail || 'Error al subir factura.' });
      throw err;
    }
  },

  retryInvoice: async (id) => {
    try {
      await invoiceApi.retry(id);
      // Refresh the detail after retry
      get().fetchInvoiceDetail(id);
    } catch (err) {
      const apiErr = err as ApiError;
      set({ detailError: apiErr.detail || 'Error al reintentar procesamiento.' });
    }
  },

  setFilters: (newFilters) => {
    set((state) => ({
      filters: { ...state.filters, ...newFilters },
      page: 1, // Reset to first page on filter change
    }));
    get().fetchInvoices();
  },

  setPage: (page) => {
    set({ page });
    get().fetchInvoices({ page });
  },

  clearUploadState: () => {
    set({ uploading: false, uploadError: null, uploadResult: null });
  },

  clearCurrentInvoice: () => {
    set({ currentInvoice: null, detailError: null });
  },
}));
