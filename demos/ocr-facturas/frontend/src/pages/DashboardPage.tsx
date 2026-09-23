import { useEffect } from 'react';
import { FileText, DollarSign, TrendingUp, Receipt } from 'lucide-react';
import { useDashboardStore, defaultStats } from '../stores/useDashboardStore';
import { formatCurrency } from '../utils/formatters';
import StatCard from '../components/dashboard/StatCard';
import ChartCard from '../components/dashboard/ChartCard';
import InvoiceTypeBreakdown from '../components/dashboard/InvoiceTypeBreakdown';
import TopSuppliersList from '../components/dashboard/TopSuppliersList';
import MonthlyTrendChart from '../components/dashboard/MonthlyTrendChart';
import StatusSummary from '../components/dashboard/StatusSummary';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

export default function DashboardPage() {
  const { stats, loading, error, fetchStats } = useDashboardStore();

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  if (loading && !stats) {
    return <LoadingSpinner size="lg" text="Cargando estadísticas..." className="py-20" />;
  }

  if (error && !stats) {
    return <ErrorMessage message={error} onRetry={fetchStats} />;
  }

  // Use stats if available, otherwise fall back to defaultStats (all zeros)
  const displayStats = stats ?? defaultStats;

  return (
    <div className="space-y-6">
      {/* Stat Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Facturas"
          value={displayStats.total_invoices.toString()}
          subtitle="Facturas procesadas"
          icon={<FileText className="h-5 w-5" />}
        />
        <StatCard
          title="Gasto Total"
          value={formatCurrency(displayStats.total_spending)}
          subtitle="Todas las facturas"
          icon={<DollarSign className="h-5 w-5" />}
        />
        <StatCard
          title="Promedio"
          value={formatCurrency(displayStats.average_invoice_amount)}
          subtitle="Monto promedio por factura"
          icon={<TrendingUp className="h-5 w-5" />}
        />
        <StatCard
          title="IVA Total"
          value={formatCurrency(
            Object.values(displayStats.status_summary).reduce((a, b) => a + b, 0),
          )}
          subtitle="Resumen de estados"
          icon={<Receipt className="h-5 w-5" />}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartCard title="Facturas por Tipo">
          <InvoiceTypeBreakdown data={displayStats.invoices_by_type} />
        </ChartCard>
        <ChartCard title="Top Proveedores">
          <TopSuppliersList suppliers={displayStats.top_suppliers} />
        </ChartCard>
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <ChartCard title="Tendencia Mensual">
          <MonthlyTrendChart data={displayStats.monthly_trend} />
        </ChartCard>
        <ChartCard title="Resumen de Estados">
          <StatusSummary data={displayStats.status_summary} />
        </ChartCard>
      </div>
    </div>
  );
}
