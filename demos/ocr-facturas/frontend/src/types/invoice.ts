// Invoice status type
export type InvoiceStatus = 'processing' | 'completed' | 'failed';

// Invoice type letter (Argentine invoice types)
export type InvoiceType = 'A' | 'B' | 'C' | 'E' | 'M';

// Invoice summary for list view
export interface InvoiceSummary {
  id: string;
  status: InvoiceStatus;
  invoice_type: InvoiceType | null;
  invoice_code: string | null;
  point_of_sale: string | null;
  invoice_number: string | null;
  complete_number: string | null;
  issue_date: string | null;
  currency: string | null;
  cae: string | null;
  original_filename: string;
  file_size_bytes: number;
  created_at: string;
  processed_at: string | null;
  // Joined data for list display
  issuer_name?: string | null;
  total_amount?: number | null;
}

// Invoice issuer
export interface InvoiceIssuer {
  id: string;
  invoice_id: string;
  fantasy_name: string | null;
  legal_name: string | null;
  cuit: string | null;
  fiscal_condition: string | null;
  address: string | null;
  locality: string | null;
  province: string | null;
  postal_code: string | null;
  phone: string | null;
  activity_start: string | null;
}

// Invoice client
export interface InvoiceClient {
  id: string;
  invoice_id: string;
  legal_name: string | null;
  document_type: string | null;
  document_number: string | null;
  fiscal_condition: string | null;
  address: string | null;
  locality: string | null;
  province: string | null;
  postal_code: string | null;
  phone: string | null;
  sale_condition: string | null;
}

// Invoice line item
export interface InvoiceLineItem {
  id: string;
  invoice_id: string;
  line_order: number;
  product_code: string | null;
  description: string | null;
  quantity: number | null;
  unit: string | null;
  unit_price: number | null;
  discount: number | null;
  subtotal_without_iva: number | null;
  iva_rate: string | null;
  total_with_iva: number | null;
}

// IVA detail entry
export interface IVADetailEntry {
  rate: string;
  amount: number;
}

// Invoice totals
export interface InvoiceTotals {
  id: string;
  invoice_id: string;
  net_amount: number | null;
  iva_amount: number | null;
  iva_detail: IVADetailEntry[] | null;
  other_taxes: number | null;
  total_invoice_currency: number | null;
  total_ars: number | null;
}

// Full invoice detail
export interface InvoiceDetail {
  id: string;
  status: InvoiceStatus;
  invoice_type: InvoiceType | null;
  invoice_code: string | null;
  point_of_sale: string | null;
  invoice_number: string | null;
  complete_number: string | null;
  issue_date: string | null;
  currency: string | null;
  exchange_rate: string | null;
  cae: string | null;
  cae_expiry_date: string | null;
  original_filename: string;
  file_size_bytes: number;
  file_path: string;
  ocr_status_code: number | null;
  text_blocks_count: number | null;
  validation_warnings: string[] | null;
  created_at: string;
  processed_at: string | null;
  issuer: InvoiceIssuer | null;
  client: InvoiceClient | null;
  line_items: InvoiceLineItem[];
  totals: InvoiceTotals | null;
}

// Upload response
export interface InvoiceUploadResponse {
  invoice_id: string;
  status: InvoiceStatus;
}

// Retry response
export interface InvoiceRetryResponse {
  invoice_id: string;
  status: InvoiceStatus;
}

// Invoice list parameters
export interface InvoiceListParams {
  page?: number;
  page_size?: number;
  status?: InvoiceStatus | '';
  invoice_type?: InvoiceType | '';
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}
