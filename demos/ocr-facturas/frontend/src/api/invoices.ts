import apiClient from './apiClient';
import type {
  InvoiceSummary,
  InvoiceDetail,
  InvoiceUploadResponse,
  InvoiceRetryResponse,
  InvoiceListParams,
} from '../types/invoice';
import type { PaginatedResponse } from '../types/api';

export const invoiceApi = {
  /**
   * Upload an invoice file for OCR processing
   */
  upload: async (file: File): Promise<InvoiceUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<InvoiceUploadResponse>('/invoices/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000, // OCR can take up to 120s
    });
    return response.data;
  },

  /**
   * Get paginated list of invoices
   */
  list: async (params: InvoiceListParams = {}): Promise<PaginatedResponse<InvoiceSummary>> => {
    const queryParams: Record<string, string | number> = {};
    if (params.page) queryParams.page = params.page;
    if (params.page_size) queryParams.page_size = params.page_size;
    if (params.status) queryParams.status = params.status;
    if (params.invoice_type) queryParams.invoice_type = params.invoice_type;
    if (params.sort_by) queryParams.sort_by = params.sort_by;
    if (params.sort_order) queryParams.sort_order = params.sort_order;

    const response = await apiClient.get<PaginatedResponse<InvoiceSummary>>('/invoices/', {
      params: queryParams,
    });
    return response.data;
  },

  /**
   * Get full invoice detail by ID
   */
  detail: async (id: string): Promise<InvoiceDetail> => {
    const response = await apiClient.get<InvoiceDetail>(`/invoices/${id}`);
    return response.data;
  },

  /**
   * Retry OCR processing for a failed invoice
   */
  retry: async (id: string): Promise<InvoiceRetryResponse> => {
    const response = await apiClient.post<InvoiceRetryResponse>(`/invoices/${id}/retry`);
    return response.data;
  },

  /**
   * Delete an invoice
   */
  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/invoices/${id}`);
  },
};
