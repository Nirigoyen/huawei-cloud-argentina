import { useEffect } from 'react';
import { useInvoiceStore } from '../stores/useInvoiceStore';
import InvoiceTable from '../components/invoices/InvoiceTable';
import InvoiceFilters from '../components/invoices/InvoiceFilters';
import Pagination from '../components/common/Pagination';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

export default function InvoicesPage() {
  const {
    invoices,
    total,
    page,
    pageSize,
    filters,
    loading,
    error,
    fetchInvoices,
    setFilters,
    setPage,
  } = useInvoiceStore();

  useEffect(() => {
    fetchInvoices();
  }, [fetchInvoices]);

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm">
        <InvoiceFilters
          status={filters.status}
          invoiceType={filters.invoice_type}
          onStatusChange={(status) => setFilters({ status })}
          onTypeChange={(invoice_type) => setFilters({ invoice_type })}
          onClear={() => setFilters({ status: '', invoice_type: '' })}
        />
      </div>

      {/* Table */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
        {loading ? (
          <LoadingSpinner text="Cargando facturas..." className="py-12" />
        ) : error ? (
          <ErrorMessage message={error} onRetry={() => fetchInvoices()} />
        ) : (
          <>
            <InvoiceTable invoices={invoices} />
            <Pagination
              currentPage={page}
              totalPages={totalPages}
              total={total}
              pageSize={pageSize}
              onPageChange={setPage}
            />
          </>
        )}
      </div>
    </div>
  );
}
