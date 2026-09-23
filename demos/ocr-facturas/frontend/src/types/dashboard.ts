// Top supplier entry
export interface TopSupplier {
  fantasy_name: string | null;
  legal_name: string | null;
  cuit: string | null;
  total_amount: number;
}

// Monthly spending entry
export interface MonthlySpending {
  month: string; // "YYYY-MM" format
  total_amount: number;
  invoice_count: number;
}

// Dashboard statistics
export interface DashboardStats {
  total_invoices: number;
  total_spending: number;
  average_invoice_amount: number;
  invoices_by_type: Record<string, number>;
  top_suppliers: TopSupplier[];
  monthly_trend: MonthlySpending[];
  status_summary: Record<string, number>;
}
