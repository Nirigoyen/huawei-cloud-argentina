import { CheckCircle, XCircle, Clock } from 'lucide-react';

interface StatusSummaryProps {
  data: Record<string, number>;
}

const statusConfig: Record<string, { label: string; icon: typeof CheckCircle; color: string }> = {
  completed: { label: 'Completadas', icon: CheckCircle, color: 'text-success-600 bg-success-50' },
  failed: { label: 'Fallidas', icon: XCircle, color: 'text-danger-600 bg-danger-50' },
  processing: { label: 'Procesando', icon: Clock, color: 'text-warning-600 bg-warning-50' },
};

export default function StatusSummary({ data }: StatusSummaryProps) {
  const entries = Object.entries(data).filter(([key]) => key in statusConfig);
  const totalInvoices = entries.reduce((sum, [, value]) => sum + value, 0);

  if (entries.length === 0 || totalInvoices === 0) {
    return <p className="text-sm text-gray-500">No hay facturas procesadas.</p>;
  }

  return (
    <div className="space-y-3">
      {entries.map(([key, value]) => {
        const config = statusConfig[key];
        const Icon = config.icon;
        return (
          <div key={key} className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={`rounded-md p-1.5 ${config.color}`}>
                <Icon className="h-4 w-4" />
              </div>
              <span className="text-sm text-gray-700">{config.label}</span>
            </div>
            <span className="text-sm font-semibold text-gray-900">{value}</span>
          </div>
        );
      })}
    </div>
  );
}
