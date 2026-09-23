import { AlertCircle } from 'lucide-react';

interface ErrorMessageProps {
  message: string | null;
  onRetry?: () => void;
  className?: string;
}

export default function ErrorMessage({ message, onRetry, className = '' }: ErrorMessageProps) {
  if (!message) return null;

  return (
    <div
      className={`flex items-start gap-3 rounded-lg border border-danger-500/20 bg-danger-50 p-4 ${className}`}
    >
      <AlertCircle className="h-5 w-5 shrink-0 text-danger-500" />
      <div className="flex-1">
        <p className="text-sm text-danger-600">{message}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2 text-sm font-medium text-danger-600 underline hover:text-danger-500"
          >
            Reintentar
          </button>
        )}
      </div>
    </div>
  );
}
