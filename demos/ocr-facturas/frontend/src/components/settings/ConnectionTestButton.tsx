import type { ConnectionTestState, ServiceName } from '../../types/settings';
import { CheckCircle, XCircle, Loader2, Zap } from 'lucide-react';

interface ConnectionTestButtonProps {
  service: ServiceName;
  label: string;
  testState: ConnectionTestState;
  onTest: () => void;
}

const statusRenderers = {
  idle: () => null,
  testing: () => (
    <div className="flex items-center gap-2 text-sm text-primary-600">
      <Loader2 className="h-4 w-4 animate-spin" />
      <span>Probando...</span>
    </div>
  ),
  success: (state: ConnectionTestState) => (
    <div className="flex items-center gap-2 text-sm text-success-600">
      <CheckCircle className="h-4 w-4" />
      <span>Conexión exitosa</span>
      {state.latency_ms !== null && (
        <span className="text-xs text-gray-500">({state.latency_ms}ms)</span>
      )}
    </div>
  ),
  failure: (state: ConnectionTestState) => (
    <div className="flex items-center gap-2 text-sm text-danger-600">
      <XCircle className="h-4 w-4" />
      <span>{state.message || 'Error de conexión'}</span>
    </div>
  ),
};

export default function ConnectionTestButton({ testState, onTest }: ConnectionTestButtonProps) {
  const isTesting = testState.status === 'testing';
  const renderer = statusRenderers[testState.status];

  return (
    <div className="flex items-center justify-between gap-4">
      <div className="flex-1">
        {testState.status === 'idle' ? (
          <p className="text-sm text-gray-500">Hacé clic para probar la conexión.</p>
        ) : (
          renderer(testState)
        )}
      </div>
      <button
        onClick={onTest}
        disabled={isTesting}
        className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
      >
        <Zap className="h-4 w-4" />
        {isTesting ? 'Probando...' : 'Probar'}
      </button>
    </div>
  );
}
