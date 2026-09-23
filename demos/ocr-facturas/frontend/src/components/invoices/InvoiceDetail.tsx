import type { InvoiceDetail as InvoiceDetailType } from '../../types/invoice';
import { formatCurrency, formatDate, formatCUIT, formatNumber } from '../../utils/formatters';
import { CheckCircle, XCircle, Clock, AlertTriangle, RotateCcw, FileText } from 'lucide-react';

interface InvoiceDetailProps {
  invoice: InvoiceDetailType;
  onRetry?: () => void;
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

export default function InvoiceDetail({ invoice, onRetry }: InvoiceDetailProps) {
  const config = statusConfig[invoice.status];
  const StatusIcon = config.icon;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-primary-50 p-3">
              <FileText className="h-6 w-6 text-primary-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">
                Factura {invoice.invoice_type || ''} {invoice.complete_number || ''}
              </h2>
              <p className="text-sm text-gray-500">{invoice.original_filename}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span
              className={`inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm font-medium ${config.bg} ${config.color}`}
            >
              <StatusIcon className="h-4 w-4" />
              {config.label}
            </span>
            {invoice.status === 'failed' && onRetry && (
              <button
                onClick={onRetry}
                className="inline-flex items-center gap-1 rounded-md bg-primary-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-primary-700"
              >
                <RotateCcw className="h-4 w-4" />
                Reintentar
              </button>
            )}
          </div>
        </div>

        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div>
            <p className="text-xs text-gray-500">Punto de Venta</p>
            <p className="text-sm font-medium">{invoice.point_of_sale || '-'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Número</p>
            <p className="text-sm font-medium">{invoice.invoice_number || '-'}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Fecha de Emisión</p>
            <p className="text-sm font-medium">{formatDate(invoice.issue_date)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500">Moneda</p>
            <p className="text-sm font-medium">{invoice.currency || '-'}</p>
          </div>
          {invoice.invoice_code && (
            <div>
              <p className="text-xs text-gray-500">Código</p>
              <p className="text-sm font-medium">{invoice.invoice_code}</p>
            </div>
          )}
          {invoice.exchange_rate && (
            <div>
              <p className="text-xs text-gray-500">Tipo de Cambio</p>
              <p className="text-sm font-medium">{invoice.exchange_rate}</p>
            </div>
          )}
        </div>
      </div>

      {/* Validation Warnings */}
      {invoice.validation_warnings && invoice.validation_warnings.length > 0 && (
        <div className="rounded-xl border border-warning-500/20 bg-warning-50 p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-5 w-5 text-warning-600" />
            <h3 className="text-sm font-semibold text-warning-600">Advertencias de Validación</h3>
          </div>
          <ul className="list-disc list-inside space-y-1">
            {invoice.validation_warnings.map((w, i) => (
              <li key={i} className="text-sm text-warning-600">
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Issuer */}
      {invoice.issuer && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-sm font-semibold text-gray-900">Datos del Emisor</h3>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <div>
              <p className="text-xs text-gray-500">Razón Social</p>
              <p className="text-sm font-medium">{invoice.issuer.legal_name || '-'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Nombre de Fantasía</p>
              <p className="text-sm font-medium">{invoice.issuer.fantasy_name || '-'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">CUIT</p>
              <p className="text-sm font-medium">{formatCUIT(invoice.issuer.cuit)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Condición Fiscal</p>
              <p className="text-sm font-medium">{invoice.issuer.fiscal_condition || '-'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Dirección</p>
              <p className="text-sm font-medium">{invoice.issuer.address || '-'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Localidad</p>
              <p className="text-sm font-medium">
                {[invoice.issuer.locality, invoice.issuer.province].filter(Boolean).join(', ') ||
                  '-'}
              </p>
            </div>
            {invoice.issuer.phone && (
              <div>
                <p className="text-xs text-gray-500">Teléfono</p>
                <p className="text-sm font-medium">{invoice.issuer.phone}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Client */}
      {invoice.client && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-sm font-semibold text-gray-900">Datos del Cliente</h3>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            <div>
              <p className="text-xs text-gray-500">Razón Social</p>
              <p className="text-sm font-medium">{invoice.client.legal_name || '-'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Documento</p>
              <p className="text-sm font-medium">
                {invoice.client.document_type && invoice.client.document_number
                  ? `${invoice.client.document_type}: ${invoice.client.document_number}`
                  : '-'}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Condición Fiscal</p>
              <p className="text-sm font-medium">{invoice.client.fiscal_condition || '-'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Condición de Venta</p>
              <p className="text-sm font-medium">{invoice.client.sale_condition || '-'}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500">Dirección</p>
              <p className="text-sm font-medium">{invoice.client.address || '-'}</p>
            </div>
          </div>
        </div>
      )}

      {/* Line Items */}
      {invoice.line_items.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-sm font-semibold text-gray-900">Productos / Servicios</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">#</th>
                  <th className="px-3 py-2 text-left text-xs font-medium text-gray-500">
                    Descripción
                  </th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">
                    Cantidad
                  </th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">
                    Precio Unit.
                  </th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">
                    Subtotal
                  </th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">IVA</th>
                  <th className="px-3 py-2 text-right text-xs font-medium text-gray-500">
                    Total c/IVA
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {invoice.line_items.map((item) => (
                  <tr key={item.id}>
                    <td className="px-3 py-2 text-sm text-gray-500">{item.line_order}</td>
                    <td className="px-3 py-2 text-sm text-gray-900">{item.description || '-'}</td>
                    <td className="px-3 py-2 text-right text-sm text-gray-500">
                      {item.quantity ?? '-'}
                    </td>
                    <td className="px-3 py-2 text-right text-sm text-gray-500">
                      {formatNumber(item.unit_price)}
                    </td>
                    <td className="px-3 py-2 text-right text-sm text-gray-500">
                      {formatNumber(item.subtotal_without_iva)}
                    </td>
                    <td className="px-3 py-2 text-right text-sm text-gray-500">
                      {item.iva_rate || '-'}
                    </td>
                    <td className="px-3 py-2 text-right text-sm font-medium text-gray-900">
                      {formatNumber(item.total_with_iva)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Totals */}
      {invoice.totals && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-sm font-semibold text-gray-900">Totales</h3>
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">Neto</span>
              <span className="font-medium">{formatCurrency(invoice.totals.net_amount)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-gray-500">IVA</span>
              <span className="font-medium">{formatCurrency(invoice.totals.iva_amount)}</span>
            </div>
            {invoice.totals.iva_detail &&
              invoice.totals.iva_detail.map((d, i) => (
                <div key={i} className="flex justify-between text-xs pl-4">
                  <span className="text-gray-400">IVA {d.rate}</span>
                  <span className="text-gray-500">{formatNumber(d.amount)}</span>
                </div>
              ))}
            {invoice.totals.other_taxes !== null && invoice.totals.other_taxes > 0 && (
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Otros Impuestos</span>
                <span className="font-medium">{formatCurrency(invoice.totals.other_taxes)}</span>
              </div>
            )}
            <div className="flex justify-between border-t border-gray-200 pt-2 text-sm font-bold">
              <span>Total</span>
              <span className="text-primary-600">{formatCurrency(invoice.totals.total_ars)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Authorization (CAE) */}
      {invoice.cae && (
        <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
          <h3 className="mb-4 text-sm font-semibold text-gray-900">Autorización (CAE)</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-gray-500">CAE</p>
              <p className="text-sm font-medium font-mono">{invoice.cae}</p>
            </div>
            {invoice.cae_expiry_date && (
              <div>
                <p className="text-xs text-gray-500">Vencimiento CAE</p>
                <p className="text-sm font-medium">{formatDate(invoice.cae_expiry_date)}</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
