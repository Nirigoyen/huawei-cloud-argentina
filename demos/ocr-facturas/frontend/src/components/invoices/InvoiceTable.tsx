import { useNavigate } from 'react-router-dom';
import { CheckCircle, XCircle, Clock, Eye, FileText } from 'lucide-react';
import type { InvoiceSummary } from '../../types/invoice';
import { formatCurrency, formatDate, formatInvoiceNumber } from '../../utils/formatters';

interface InvoiceTableProps {
  invoices: InvoiceSummary[];
}

const statusConfig = {
  completed: {
    icon: CheckCircle,
    color: 'text-success-600',
    bg: 'bg-success-50',
    label: 'Completada',
  },
  failed: { icon: XCircle, color: 'text-danger-600', bg: 'bg-danger-50', label: 'Fallida' },
  processing: { icon: Clock, color: 'text-warning-600', bg: 'bg-warning-50', label: 'Procesando' },
};

export default function InvoiceTable({ invoices }: InvoiceTableProps) {
  const navigate = useNavigate();

  if (invoices.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <div className="rounded-full bg-gray-100 p-6">
          <FileText className="h-10 w-10 text-gray-400" />
        </div>
        <h3 className="mt-4 text-base font-semibold text-gray-900">No hay facturas</h3>
        <p className="mt-1 text-sm text-gray-500">
          Aún no se han procesado facturas. Subí una factura para comenzar.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Número
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Tipo
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Emisor
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              Fecha
            </th>
            <th className="px-4 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500">
              Total
            </th>
            <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
              Estado
            </th>
            <th className="px-4 py-3 text-center text-xs font-medium uppercase tracking-wider text-gray-500">
              Acciones
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 bg-white">
          {invoices.map((invoice) => {
            const config = statusConfig[invoice.status];
            const StatusIcon = config.icon;
            return (
              <tr key={invoice.id} className="hover:bg-gray-50">
                <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900">
                  {invoice.complete_number ||
                    formatInvoiceNumber(invoice.point_of_sale, invoice.invoice_number) ||
                    '-'}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                  {invoice.invoice_type ? `Tipo ${invoice.invoice_type}` : '-'}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                  {invoice.issuer_name || '-'}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500">
                  {formatDate(invoice.issue_date)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-right text-sm font-medium text-gray-900">
                  {formatCurrency(invoice.total_amount)}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-center">
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${config.bg} ${config.color}`}
                  >
                    <StatusIcon className="h-3 w-3" />
                    {config.label}
                  </span>
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-center">
                  <button
                    onClick={() => navigate(`/invoices/${invoice.id}`)}
                    className="rounded-md p-1 text-gray-400 hover:bg-primary-50 hover:text-primary-600"
                    title="Ver detalle"
                  >
                    <Eye className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
