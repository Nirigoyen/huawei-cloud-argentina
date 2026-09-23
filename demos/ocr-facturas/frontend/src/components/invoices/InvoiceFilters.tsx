import { Filter, X } from 'lucide-react';
import type { InvoiceStatus, InvoiceType } from '../../types/invoice';

interface InvoiceFiltersProps {
  status: InvoiceStatus | '';
  invoiceType: InvoiceType | '';
  onStatusChange: (status: InvoiceStatus | '') => void;
  onTypeChange: (type: InvoiceType | '') => void;
  onClear: () => void;
}

export default function InvoiceFilters({
  status,
  invoiceType,
  onStatusChange,
  onTypeChange,
  onClear,
}: InvoiceFiltersProps) {
  const hasFilters = status !== '' || invoiceType !== '';

  return (
    <div className="flex flex-wrap items-center gap-3">
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <Filter className="h-4 w-4" />
        <span>Filtros:</span>
      </div>

      <select
        value={status}
        onChange={(e) => onStatusChange(e.target.value as InvoiceStatus | '')}
        className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
      >
        <option value="">Todos los estados</option>
        <option value="completed">Completadas</option>
        <option value="processing">Procesando</option>
        <option value="failed">Fallidas</option>
      </select>

      <select
        value={invoiceType}
        onChange={(e) => onTypeChange(e.target.value as InvoiceType | '')}
        className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
      >
        <option value="">Todos los tipos</option>
        <option value="A">Tipo A</option>
        <option value="B">Tipo B</option>
        <option value="C">Tipo C</option>
        <option value="E">Tipo E</option>
        <option value="M">Tipo M</option>
      </select>

      {hasFilters && (
        <button
          onClick={onClear}
          className="inline-flex items-center gap-1 rounded-md bg-gray-100 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200"
        >
          <X className="h-3 w-3" />
          Limpiar
        </button>
      )}
    </div>
  );
}
