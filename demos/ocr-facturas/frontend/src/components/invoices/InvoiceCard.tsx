import { useNavigate } from 'react-router-dom';
import { FileText, CheckCircle, XCircle, Clock } from 'lucide-react';
import type { InvoiceSummary } from '../../types/invoice';
import { formatCurrency, formatDate, formatInvoiceNumber } from '../../utils/formatters';

interface InvoiceCardProps {
  invoice: InvoiceSummary;
}

const statusIcons = {
  completed: CheckCircle,
  failed: XCircle,
  processing: Clock,
};

const statusColors = {
  completed: 'text-success-600',
  failed: 'text-danger-600',
  processing: 'text-warning-600',
};

const statusLabels = {
  completed: 'Completada',
  failed: 'Fallida',
  processing: 'Procesando',
};

export default function InvoiceCard({ invoice }: InvoiceCardProps) {
  const navigate = useNavigate();
  const StatusIcon = statusIcons[invoice.status];

  return (
    <div
      onClick={() => navigate(`/invoices/${invoice.id}`)}
      className="cursor-pointer rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-all hover:border-primary-300 hover:shadow-md"
    >
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-primary-50 p-2">
            <FileText className="h-5 w-5 text-primary-600" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">
              {invoice.complete_number ||
                formatInvoiceNumber(invoice.point_of_sale, invoice.invoice_number) ||
                'Sin número'}
            </p>
            <p className="text-xs text-gray-500">{invoice.issuer_name || 'Emisor desconocido'}</p>
          </div>
        </div>
        <div className={`flex items-center gap-1 ${statusColors[invoice.status]}`}>
          <StatusIcon className="h-4 w-4" />
          <span className="text-xs font-medium">{statusLabels[invoice.status]}</span>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
        <span>{formatDate(invoice.issue_date)}</span>
        <span className="font-semibold text-gray-900">{formatCurrency(invoice.total_amount)}</span>
      </div>
      {invoice.invoice_type && (
        <div className="mt-2">
          <span className="inline-flex items-center rounded-full bg-primary-50 px-2 py-0.5 text-xs font-medium text-primary-700">
            Tipo {invoice.invoice_type}
          </span>
        </div>
      )}
    </div>
  );
}
