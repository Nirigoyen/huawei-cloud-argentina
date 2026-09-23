import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { useInvoiceStore } from '../stores/useInvoiceStore';
import InvoiceDetail from '../components/invoices/InvoiceDetail';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';

export default function InvoiceDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const {
    currentInvoice,
    detailLoading,
    detailError,
    fetchInvoiceDetail,
    retryInvoice,
    clearCurrentInvoice,
  } = useInvoiceStore();

  useEffect(() => {
    if (id) {
      fetchInvoiceDetail(id);
    }
    return () => clearCurrentInvoice();
  }, [id, fetchInvoiceDetail, clearCurrentInvoice]);

  if (detailLoading) {
    return <LoadingSpinner size="lg" text="Cargando detalle de factura..." className="py-20" />;
  }

  if (detailError) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => navigate('/invoices')}
          className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
        >
          <ArrowLeft className="h-4 w-4" />
          Volver a facturas
        </button>
        <ErrorMessage message={detailError} onRetry={() => id && fetchInvoiceDetail(id)} />
      </div>
    );
  }

  if (!currentInvoice) return null;

  return (
    <div className="space-y-4">
      <button
        onClick={() => navigate('/invoices')}
        className="inline-flex items-center gap-1 text-sm text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="h-4 w-4" />
        Volver a facturas
      </button>
      <InvoiceDetail invoice={currentInvoice} onRetry={() => retryInvoice(currentInvoice.id)} />
    </div>
  );
}
