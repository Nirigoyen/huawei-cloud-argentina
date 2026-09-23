import { CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { formatFileSize } from '../../utils/formatters';

interface UploadProgressProps {
  fileName: string;
  fileSize: number;
  status: 'uploading' | 'processing' | 'completed' | 'failed';
  error?: string | null;
  invoiceId?: string;
}

const statusConfig = {
  uploading: { icon: Loader2, label: 'Subiendo...', color: 'text-primary-600', animate: true },
  processing: {
    icon: Loader2,
    label: 'Procesando OCR...',
    color: 'text-warning-600',
    animate: true,
  },
  completed: { icon: CheckCircle, label: 'Completada', color: 'text-success-600', animate: false },
  failed: { icon: XCircle, label: 'Fallida', color: 'text-danger-600', animate: false },
};

export default function UploadProgress({ fileName, fileSize, status, error }: UploadProgressProps) {
  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <div className="flex items-center gap-3">
        <div className={`${config.color} ${config.animate ? 'animate-spin' : ''}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="truncate text-sm font-medium text-gray-900">{fileName}</p>
          <p className="text-xs text-gray-500">{formatFileSize(fileSize)}</p>
        </div>
        <span className={`text-sm font-medium ${config.color}`}>{config.label}</span>
      </div>

      {/* Progress bar */}
      {(status === 'uploading' || status === 'processing') && (
        <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-gray-200">
          <div
            className={`h-full rounded-full transition-all duration-1000 ${
              status === 'uploading'
                ? 'bg-primary-500 w-2/3'
                : 'bg-warning-500 w-full animate-pulse'
            }`}
          />
        </div>
      )}

      {error && <p className="mt-2 text-xs text-danger-600">{error}</p>}
    </div>
  );
}
