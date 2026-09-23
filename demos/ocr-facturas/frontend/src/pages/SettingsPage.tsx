import { useEffect } from 'react';
import { Shield } from 'lucide-react';
import { useSettingsStore } from '../stores/useSettingsStore';
import { useToastStore } from '../stores/useToastStore';
import CredentialForm from '../components/settings/CredentialForm';
import ConnectionTestButton from '../components/settings/ConnectionTestButton';
import LoadingSpinner from '../components/common/LoadingSpinner';
import ErrorMessage from '../components/common/ErrorMessage';
import type { CredentialUpdate, ServiceName } from '../types/settings';

const serviceLabels: Record<ServiceName, string> = {
  huawei_iam: 'Huawei Cloud IAM',
  dify: 'Dify Workflow',
  maas: 'MaaS (Chatbot)',
};

export default function SettingsPage() {
  const {
    credentials,
    loading,
    error,
    saving,
    saveError,
    saveSuccess,
    connectionTests,
    applyingWorkflow,
    applyWorkflowError,
    applyWorkflowSuccess,
    testingDb,
    testDbResult,
    fetchCredentials,
    saveCredentials,
    testConnection,
    applyWorkflow,
    testDestinationDb,
    clearSaveState,
    clearApplyWorkflowState,
    clearTestDbResult,
  } = useSettingsStore();

  const addToast = useToastStore((s) => s.addToast);

  useEffect(() => {
    fetchCredentials();
  }, [fetchCredentials]);

  useEffect(() => {
    if (saveSuccess) {
      addToast('success', 'Credenciales guardadas exitosamente.');
      clearSaveState();
    }
  }, [saveSuccess, addToast, clearSaveState]);

  useEffect(() => {
    if (saveError) {
      addToast('error', saveError);
      clearSaveState();
    }
  }, [saveError, addToast, clearSaveState]);

  useEffect(() => {
    if (applyWorkflowSuccess) {
      addToast('success', 'Configuración aplicada al workflow exitosamente.');
      clearApplyWorkflowState();
    }
  }, [applyWorkflowSuccess, addToast, clearApplyWorkflowState]);

  useEffect(() => {
    if (applyWorkflowError) {
      addToast('error', applyWorkflowError);
      clearApplyWorkflowState();
    }
  }, [applyWorkflowError, addToast, clearApplyWorkflowState]);

  useEffect(() => {
    if (testDbResult) {
      if (testDbResult.success) {
        addToast('success', testDbResult.message);
      } else {
        addToast('error', testDbResult.message);
      }
      clearTestDbResult();
    }
  }, [testDbResult, addToast, clearTestDbResult]);

  if (loading) {
    return <LoadingSpinner size="lg" text="Cargando configuración..." className="py-20" />;
  }

  if (error) {
    return <ErrorMessage message={error} onRetry={fetchCredentials} />;
  }

  const handleSave = (creds: CredentialUpdate) => {
    saveCredentials(creds);
  };

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Credential Form */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-lg bg-primary-50 p-2">
            <Shield className="h-5 w-5 text-primary-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Credenciales de API</h2>
            <p className="text-sm text-gray-500">
              Configurá las credenciales para los servicios externos.
            </p>
          </div>
        </div>
        <CredentialForm
          credentials={credentials}
          onSave={handleSave}
          saving={saving}
          onApplyWorkflow={applyWorkflow}
          applyingWorkflow={applyingWorkflow}
          onTestDb={testDestinationDb}
          testingDb={testingDb}
          testDbResult={testDbResult}
        />
      </div>

      {/* Connection Tests */}
      <div className="rounded-xl border border-gray-200 bg-white p-6 shadow-sm">
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900">Probar Conexiones</h2>
          <p className="text-sm text-gray-500">
            Verificá la conectividad con cada servicio configurado.
          </p>
        </div>
        <div className="space-y-4">
          {(Object.keys(serviceLabels) as ServiceName[]).map((service) => (
            <div key={service} className="rounded-lg border border-gray-100 bg-gray-50 p-4">
              <p className="mb-2 text-sm font-medium text-gray-700">{serviceLabels[service]}</p>
              <ConnectionTestButton
                service={service}
                label={serviceLabels[service]}
                testState={connectionTests[service]}
                onTest={() => testConnection(service)}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
