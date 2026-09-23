import { useState, useCallback, useEffect } from 'react';
import { ExternalLink, RefreshCw, GitMerge, AlertCircle, LogIn, Info } from 'lucide-react';
import { useSettingsStore } from '../stores/useSettingsStore';
import LoadingSpinner from '../components/common/LoadingSpinner';

const DIFY_WORKFLOW_APP_ID = 'be1879a3-fc85-499c-98e1-348d43527081';
const DEFAULT_DIFY_WEB_URL = 'http://176.52.142.209';

export default function WorkflowPage() {
  const { credentials, fetchCredentials } = useSettingsStore();
  const [iframeLoading, setIframeLoading] = useState(true);
  const [iframeError, setIframeError] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [showLoginHint, setShowLoginHint] = useState(true);

  // Fetch settings on mount so we have dify_web_url
  useEffect(() => {
    if (!credentials) {
      fetchCredentials();
    }
  }, [credentials, fetchCredentials]);

  // Determine the Dify Web URL from settings, falling back to default
  const difyWebUrl = credentials?.dify_web_url || DEFAULT_DIFY_WEB_URL;
  const workflowUrl = `${difyWebUrl}/app/${DIFY_WORKFLOW_APP_ID}/workflow`;

  const handleIframeLoad = useCallback(() => {
    setIframeLoading(false);
    setIframeError(false);
  }, []);

  const handleIframeError = useCallback(() => {
    setIframeLoading(false);
    setIframeError(true);
  }, []);

  const handleReload = useCallback(() => {
    setIframeLoading(true);
    setIframeError(false);
    setShowLoginHint(false);
    setReloadKey((prev) => prev + 1);
  }, []);

  const handleOpenNewTab = useCallback(() => {
    window.open(workflowUrl, '_blank', 'noopener,noreferrer');
  }, [workflowUrl]);

  const handleLoginDify = useCallback(() => {
    // Open Dify login page in a new tab. After the user logs in there,
    // the session cookie will be set for the Dify origin, and the iframe
    // (which loads from the same origin) will automatically use it.
    window.open(difyWebUrl, '_blank', 'noopener,noreferrer');
  }, [difyWebUrl]);

  // If no URL is configured at all (empty string), show config message
  if (credentials?.dify_web_url === '') {
    return (
      <div className="flex h-[calc(100vh-10rem)] flex-col items-center justify-center gap-4">
        <div className="rounded-full bg-gray-100 p-6">
          <GitMerge className="h-10 w-10 text-gray-400" />
        </div>
        <div className="text-center">
          <h3 className="text-lg font-semibold text-gray-900">URL de Dify Web no configurada</h3>
          <p className="mt-1 text-sm text-gray-500">
            Configurá la URL de Dify Web en la sección de{' '}
            <a href="/settings" className="text-primary-600 underline hover:text-primary-500">
              Configuración
            </a>{' '}
            para visualizar el workflow.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-10rem)] flex-col overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-gray-200 pb-3">
        <div className="flex items-center gap-2">
          <GitMerge className="h-5 w-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">Editor de Workflow</h2>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleLoginDify}
            className="inline-flex items-center gap-1.5 rounded-md bg-primary-600 px-3 py-1.5 text-sm font-medium text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            <LogIn className="h-4 w-4" />
            Iniciar sesión en Dify
          </button>
          <button
            onClick={handleOpenNewTab}
            className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            <ExternalLink className="h-4 w-4" />
            Abrir en nueva pestaña
          </button>
          <button
            onClick={handleReload}
            className="inline-flex items-center gap-1.5 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
          >
            <RefreshCw className="h-4 w-4" />
            Recargar
          </button>
        </div>
      </div>

      {/* Login hint banner */}
      {showLoginHint && (
        <div className="flex items-center gap-2 border-b border-amber-200 bg-amber-50 px-4 py-2">
          <Info className="h-4 w-4 flex-shrink-0 text-amber-600" />
          <p className="text-sm text-amber-800">
            Si ves la pantalla de login de Dify en el editor, hacé clic en{' '}
            <strong>&quot;Iniciar sesión en Dify&quot;</strong> para autenticarte en una nueva
            pestaña. Luego volvé aquí y hacé clic en <strong>&quot;Recargar&quot;</strong>.
          </p>
          <button
            onClick={() => setShowLoginHint(false)}
            className="ml-auto flex-shrink-0 text-amber-600 hover:text-amber-800"
            aria-label="Cerrar"
          >
            ×
          </button>
        </div>
      )}

      {/* Iframe Container */}
      <div className="relative flex-1">
        {/* Loading overlay */}
        {iframeLoading && (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-white/80">
            <LoadingSpinner size="lg" text="Cargando editor de workflow..." />
          </div>
        )}

        {/* Error state */}
        {iframeError && (
          <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-white">
            <div className="rounded-full bg-danger-50 p-4">
              <AlertCircle className="h-8 w-8 text-danger-500" />
            </div>
            <div className="text-center">
              <h3 className="text-base font-semibold text-gray-900">Error al cargar el editor</h3>
              <p className="mt-1 text-sm text-gray-500">
                No se pudo conectar con el editor de Dify Workflow.
              </p>
              <p className="mt-1 text-xs text-gray-400">URL: {workflowUrl}</p>
            </div>
            <button
              onClick={handleReload}
              className="mt-2 inline-flex items-center gap-1.5 rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2"
            >
              <RefreshCw className="h-4 w-4" />
              Reintentar
            </button>
          </div>
        )}

        {/* Iframe */}
        <iframe
          key={reloadKey}
          src={workflowUrl}
          onLoad={handleIframeLoad}
          onError={handleIframeError}
          title="Editor de Workflow Dify"
          style={{ border: 'none', width: '100%', height: '100%' }}
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
        />
      </div>
    </div>
  );
}
