import { useState, useEffect, useRef, type FormEvent } from 'react';
import {
  Eye,
  EyeOff,
  Save,
  Database,
  Cloud,
  GitBranch,
  MessageSquare,
  Zap,
  Loader2,
  CheckCircle2,
  XCircle,
  ChevronDown,
  RotateCcw,
} from 'lucide-react';
import type { AppSettings, CredentialUpdate, DifyModelInfo } from '../../types/settings';
import { settingsApi } from '../../api/settings';

interface CredentialFormProps {
  credentials: AppSettings | null;
  onSave: (credentials: CredentialUpdate) => void;
  saving: boolean;
  onApplyWorkflow?: () => void;
  applyingWorkflow?: boolean;
  onTestDb?: () => void;
  testingDb?: boolean;
  testDbResult?: { success: boolean; message: string } | null;
}

interface FieldConfig {
  key: keyof CredentialUpdate;
  label: string;
  type: 'text' | 'password';
  placeholder: string;
  maskedValue: string | null;
}

interface SectionConfig {
  id: string;
  icon: React.ComponentType<{ className?: string }>;
  iconBg: string;
  iconColor: string;
  title: string;
  description: string;
  fields: FieldConfig[];
}

const sections: SectionConfig[] = [
  {
    id: 'huawei-iam',
    icon: Cloud,
    iconBg: 'bg-orange-50',
    iconColor: 'text-orange-600',
    title: 'Huawei Cloud IAM',
    description: 'Credenciales para autenticación IAM y OCR de Huawei Cloud.',
    fields: [
      {
        key: 'huawei_iam_username',
        label: 'Usuario IAM',
        type: 'text',
        placeholder: 'Ingrese el usuario IAM',
        maskedValue: null,
      },
      {
        key: 'huawei_iam_password',
        label: 'Contraseña IAM',
        type: 'password',
        placeholder: 'Ingrese la contraseña IAM',
        maskedValue: '••••••••',
      },
      {
        key: 'huawei_project_id',
        label: 'ID de Proyecto (Hong-Kong)',
        type: 'text',
        placeholder: 'Ingrese el ID del proyecto',
        maskedValue: null,
      },
    ],
  },
  {
    id: 'dify-workflow',
    icon: GitBranch,
    iconBg: 'bg-green-50',
    iconColor: 'text-green-600',
    title: 'Dify Workflow',
    description: 'Configuración del flujo de trabajo de Dify para OCR.',
    fields: [
      {
        key: 'dify_api_key',
        label: 'API Key de Dify',
        type: 'password',
        placeholder: 'Ingrese la API key de Dify',
        maskedValue: '••••••••',
      },
      {
        key: 'dify_web_url',
        label: 'URL de Dify Web',
        type: 'text',
        placeholder: 'http://101.44.13.134:3001',
        maskedValue: null,
      },
    ],
  },
  {
    id: 'dify-llm',
    icon: Zap,
    iconBg: 'bg-emerald-50',
    iconColor: 'text-emerald-600',
    title: 'Dify LLM Model',
    description: 'Modelo LLM para el flujo de trabajo de Dify (independiente del chatbot).',
    fields: [
      {
        key: 'dify_llm_api_key',
        label: 'API Key',
        type: 'password',
        placeholder: 'Ingrese la API key del modelo',
        maskedValue: '••••••••',
      },
      {
        key: 'dify_llm_base_url',
        label: 'URL Base',
        type: 'text',
        placeholder: 'https://api.example.com/v1',
        maskedValue: null,
      },
      // Note: dify_llm_model_name is rendered as a combobox below, not via renderField
    ],
  },
  {
    id: 'maas-chatbot',
    icon: MessageSquare,
    iconBg: 'bg-purple-50',
    iconColor: 'text-purple-600',
    title: 'MaaS (Chatbot)',
    description: 'Configuración del servicio de modelos para el chatbot.',
    fields: [
      {
        key: 'maas_api_key',
        label: 'API Key',
        type: 'password',
        placeholder: 'Ingrese la API key de MaaS',
        maskedValue: '••••••••',
      },
      {
        key: 'maas_base_url',
        label: 'URL de MaaS',
        type: 'text',
        placeholder: 'https://maas.ap-southeast-1.myhuaweicloud.com/v1',
        maskedValue: null,
      },
      {
        key: 'maas_model_name',
        label: 'Modelo',
        type: 'text',
        placeholder: 'deepseek-v3',
        maskedValue: null,
      },
    ],
  },
];

// Destination database field configuration
interface DestDbFieldConfig {
  key: keyof CredentialUpdate;
  label: string;
  type: 'text' | 'password';
  placeholder: string;
  maskedValue: string | null;
}

const destDbFields: DestDbFieldConfig[] = [
  {
    key: 'destination_db_host',
    label: 'Host',
    type: 'text',
    placeholder: 'localhost',
    maskedValue: null,
  },
  {
    key: 'destination_db_port',
    label: 'Puerto',
    type: 'text',
    placeholder: '5432',
    maskedValue: null,
  },
  {
    key: 'destination_db_name',
    label: 'Base de Datos',
    type: 'text',
    placeholder: 'Nombre de la base de datos',
    maskedValue: null,
  },
  {
    key: 'destination_db_username',
    label: 'Usuario',
    type: 'text',
    placeholder: 'Ingrese el usuario',
    maskedValue: null,
  },
  {
    key: 'destination_db_password',
    label: 'Contraseña',
    type: 'password',
    placeholder: 'Ingrese la contraseña',
    maskedValue: '••••••••',
  },
  {
    key: 'destination_db_table',
    label: 'Tabla Destino',
    type: 'text',
    placeholder: 'invoices',
    maskedValue: null,
  },
];

export default function CredentialForm({
  credentials,
  onSave,
  saving,
  onApplyWorkflow,
  applyingWorkflow = false,
  onTestDb,
  testingDb = false,
  testDbResult = null,
}: CredentialFormProps) {
  const [formValues, setFormValues] = useState<Record<string, string>>({});
  const [showPasswords, setShowPasswords] = useState<Record<string, boolean>>({});
  const [dirty, setDirty] = useState(false);

  // Destination database specific state
  const [dbType, setDbType] = useState<string>(credentials?.destination_db_type ?? '');
  const [dataForwardEnabled, setDataForwardEnabled] = useState<boolean>(
    credentials?.data_forward_enabled ?? false,
  );
  const [dbTypeDirty, setDbTypeDirty] = useState(false);
  const [dataForwardDirty, setDataForwardDirty] = useState(false);

  // Model combobox state
  const [availableModels, setAvailableModels] = useState<DifyModelInfo[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false);
  const [modelFilter, setModelFilter] = useState('');
  const modelDropdownRef = useRef<HTMLDivElement>(null);

  // LLM Prompt state
  const [defaultPrompt, setDefaultPrompt] = useState<string>('');
  const [promptLoading, setPromptLoading] = useState(false);
  const [promptError, setPromptError] = useState<string | null>(null);

  // Fetch available models on mount
  useEffect(() => {
    const fetchModels = async () => {
      setModelsLoading(true);
      setModelsError(null);
      try {
        const response = await settingsApi.fetchDifyModels();
        setAvailableModels(response.models);
      } catch (err) {
        setModelsError('No se pudieron cargar los modelos');
        console.error('Failed to fetch Dify models:', err);
      } finally {
        setModelsLoading(false);
      }
    };
    fetchModels();
  }, []);

  // Fetch default prompt on mount
  useEffect(() => {
    const fetchPrompt = async () => {
      setPromptLoading(true);
      setPromptError(null);
      try {
        const response = await settingsApi.fetchDifyDefaultPrompt();
        setDefaultPrompt(response.prompt);
      } catch (err) {
        setPromptError('No se pudo cargar el prompt por defecto');
        console.error('Failed to fetch Dify default prompt:', err);
      } finally {
        setPromptLoading(false);
      }
    };
    fetchPrompt();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modelDropdownRef.current && !modelDropdownRef.current.contains(event.target as Node)) {
        setModelDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleChange = (key: string, value: string) => {
    setFormValues((prev) => ({ ...prev, [key]: value }));
    setDirty(true);
  };

  const togglePassword = (key: string) => {
    setShowPasswords((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleDbTypeChange = (value: string) => {
    setDbType(value);
    setDbTypeDirty(true);
    setDirty(true);
  };

  const handleDataForwardToggle = () => {
    setDataForwardEnabled((prev) => !prev);
    setDataForwardDirty(true);
    setDirty(true);
  };

  const handleModelSelect = (modelId: string) => {
    setFormValues((prev) => ({ ...prev, dify_llm_model_name: modelId }));
    setModelFilter(modelId);
    setModelDropdownOpen(false);
    setDirty(true);
  };

  const handleModelInputChange = (value: string) => {
    setFormValues((prev) => ({ ...prev, dify_llm_model_name: value }));
    setModelFilter(value);
    setModelDropdownOpen(true);
    setDirty(true);
  };

  const handlePromptChange = (value: string) => {
    setFormValues((prev) => ({ ...prev, dify_llm_prompt: value }));
    setDirty(true);
  };

  const handleResetPrompt = () => {
    // Clear the custom prompt so the default is used
    setFormValues((prev) => ({ ...prev, dify_llm_prompt: '' }));
    setDirty(true);
  };

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    const MASK = '••••••••';
    const update: CredentialUpdate = {};
    for (const [key, value] of Object.entries(formValues)) {
      if (value.trim() !== '' && value !== MASK) {
        (update as Record<string, string>)[key] = value.trim();
      }
    }
    // Include dify_llm_prompt even if empty (to reset to default)
    if ('dify_llm_prompt' in formValues) {
      update.dify_llm_prompt = formValues.dify_llm_prompt.trim();
    }
    // Include destination DB type if changed
    if (dbTypeDirty && dbType) {
      update.destination_db_type = dbType;
    }
    // Include data forward enabled if changed
    if (dataForwardDirty) {
      update.data_forward_enabled = dataForwardEnabled;
    }
    onSave(update);
    setFormValues({});
    setDirty(false);
    setDbTypeDirty(false);
    setDataForwardDirty(false);
  };

  const getDisplayValue = (field: FieldConfig | DestDbFieldConfig): string => {
    // If user has typed a new value, show it
    if (formValues[field.key] !== undefined) {
      return formValues[field.key];
    }
    // If credentials are loaded and the field has a masked value
    if (credentials) {
      const credValue = credentials[field.key as keyof AppSettings];
      if (credValue) {
        return field.maskedValue || String(credValue);
      }
    }
    return '';
  };

  const getModelDisplayValue = (): string => {
    if (formValues['dify_llm_model_name'] !== undefined) {
      return formValues['dify_llm_model_name'];
    }
    if (credentials?.dify_llm_model_name) {
      return credentials.dify_llm_model_name;
    }
    return '';
  };

  const getPromptDisplayValue = (): string => {
    if (formValues['dify_llm_prompt'] !== undefined) {
      return formValues['dify_llm_prompt'];
    }
    // If the user has a saved custom prompt, show it
    if (credentials?.dify_llm_prompt) {
      return credentials.dify_llm_prompt;
    }
    return '';
  };

  const inputClassName =
    'w-full rounded-md border border-gray-300 px-3 py-2 pr-10 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500';

  const renderField = (field: FieldConfig | DestDbFieldConfig) => {
    const isPassword = field.type === 'password';
    const showPassword = showPasswords[field.key];
    const hasValue = credentials?.[field.key as keyof AppSettings] !== null;

    return (
      <div key={field.key} className="mb-4">
        <label className="mb-1 block text-sm font-medium text-gray-700">
          {field.label}
          {hasValue && !formValues[field.key] && (
            <span className="ml-2 text-xs text-success-600">✓ Configurado</span>
          )}
        </label>
        <div className="relative">
          <input
            type={isPassword && !showPassword ? 'password' : 'text'}
            value={getDisplayValue(field)}
            onChange={(e) => handleChange(field.key, e.target.value)}
            placeholder={field.placeholder}
            className={inputClassName}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => togglePassword(field.key)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          )}
        </div>
      </div>
    );
  };

  // Filter models for dropdown
  const filteredModels = availableModels.filter(
    (m) =>
      m.id.toLowerCase().includes(modelFilter.toLowerCase()) ||
      m.name.toLowerCase().includes(modelFilter.toLowerCase()),
  );

  const currentModelValue = getModelDisplayValue();

  return (
    <form onSubmit={handleSubmit} className="space-y-0">
      {/* Section 1: Huawei Cloud IAM */}
      {sections.map((section, sectionIndex) => {
        const SectionIcon = section.icon;
        return (
          <div
            key={section.id}
            className={sectionIndex > 0 ? 'border-t border-gray-200 pt-6' : 'pt-2'}
          >
            <div className="mb-5 flex items-center gap-3">
              <div className={`rounded-lg ${section.iconBg} p-2`}>
                <SectionIcon className={`h-5 w-5 ${section.iconColor}`} />
              </div>
              <div>
                <h3 className="text-base font-semibold text-gray-900">{section.title}</h3>
                <p className="text-sm text-gray-500">{section.description}</p>
              </div>
            </div>
            {section.fields.map(renderField)}

            {/* Model Combobox for Dify LLM section */}
            {section.id === 'dify-llm' && (
              <>
                {/* Model Combobox */}
                <div className="mb-4">
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Modelo
                    {credentials?.dify_llm_model_name && !formValues['dify_llm_model_name'] && (
                      <span className="ml-2 text-xs text-success-600">✓ Configurado</span>
                    )}
                  </label>
                  <div className="relative" ref={modelDropdownRef}>
                    <div className="relative">
                      <input
                        type="text"
                        value={modelFilter || currentModelValue}
                        onChange={(e) => handleModelInputChange(e.target.value)}
                        onFocus={() => setModelDropdownOpen(true)}
                        placeholder="Seleccione o escriba un modelo"
                        className={inputClassName.replace('pr-10', 'pr-8')}
                      />
                      <button
                        type="button"
                        onClick={() => setModelDropdownOpen(!modelDropdownOpen)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {modelsLoading ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </button>
                    </div>
                    {/* Dropdown */}
                    {modelDropdownOpen && !modelsLoading && (
                      <div className="absolute z-10 mt-1 max-h-60 w-full overflow-auto rounded-md border border-gray-200 bg-white py-1 shadow-lg">
                        {modelsError && (
                          <div className="px-3 py-2 text-xs text-red-500">{modelsError}</div>
                        )}
                        {filteredModels.length === 0 && !modelsError && (
                          <div className="px-3 py-2 text-xs text-gray-500">
                            No se encontraron modelos
                          </div>
                        )}
                        {filteredModels.map((model) => (
                          <button
                            key={model.id}
                            type="button"
                            onClick={() => handleModelSelect(model.id)}
                            className={`w-full px-3 py-2 text-left text-sm hover:bg-primary-50 ${
                              model.id === currentModelValue
                                ? 'bg-primary-50 font-medium text-primary-700'
                                : 'text-gray-700'
                            }`}
                          >
                            <span>{model.name}</span>
                            <span className="ml-2 text-xs text-gray-400">({model.type})</span>
                            {model.status !== 'active' && (
                              <span className="ml-2 text-xs text-amber-500">{model.status}</span>
                            )}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  {modelsError && <p className="mt-1 text-xs text-red-500">{modelsError}</p>}
                </div>

                {/* LLM Prompt Textarea */}
                <div className="mb-4">
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Prompt del LLM
                  </label>
                  <textarea
                    value={getPromptDisplayValue()}
                    onChange={(e) => handlePromptChange(e.target.value)}
                    placeholder={
                      promptLoading
                        ? 'Cargando prompt por defecto...'
                        : defaultPrompt || 'Ingrese el prompt del LLM'
                    }
                    rows={12}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 font-mono"
                  />
                  <div className="mt-1 flex items-center justify-between">
                    <p className="text-xs text-gray-500">
                      Dejar vacío para usar el prompt por defecto
                    </p>
                    <button
                      type="button"
                      onClick={handleResetPrompt}
                      className="inline-flex items-center gap-1 text-xs text-gray-500 hover:text-primary-600"
                      title="Restablecer al prompt por defecto"
                    >
                      <RotateCcw className="h-3 w-3" />
                      Restablecer
                    </button>
                  </div>
                  {promptError && <p className="mt-1 text-xs text-red-500">{promptError}</p>}
                </div>
              </>
            )}
          </div>
        );
      })}

      {/* Section 4: Destination Database */}
      <div className="border-t border-gray-200 pt-6">
        <div className="mb-5 flex items-center gap-3">
          <div className="rounded-lg bg-blue-50 p-2">
            <Database className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-gray-900">Base de Datos Destino</h3>
            <p className="text-sm text-gray-500">
              Configure una base de datos destino para reenviar los datos extraídos de las facturas.
            </p>
          </div>
        </div>

        {/* Database Type Selector */}
        <div className="mb-4">
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Tipo de Base de Datos
          </label>
          <select
            value={dbType}
            onChange={(e) => handleDbTypeChange(e.target.value)}
            className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          >
            <option value="">Seleccionar...</option>
            <option value="postgresql">PostgreSQL</option>
            <option value="mysql">MySQL</option>
          </select>
        </div>

        {/* Destination DB Text/Password Fields */}
        {destDbFields.map(renderField)}

        {/* Data Forward Enabled Toggle */}
        <div className="mb-4 flex items-center gap-3">
          <button
            type="button"
            role="switch"
            aria-checked={dataForwardEnabled}
            onClick={handleDataForwardToggle}
            className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
              dataForwardEnabled ? 'bg-primary-600' : 'bg-gray-200'
            }`}
          >
            <span
              className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out ${
                dataForwardEnabled ? 'translate-x-5' : 'translate-x-0'
              }`}
            />
          </button>
          <label className="text-sm font-medium text-gray-700">Habilitar Reenvío de Datos</label>
        </div>

        {/* Data Forward URL */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">
            URL de Reenvío de Datos
          </label>
          <input
            type="text"
            value={
              formValues['data_forward_url'] !== undefined
                ? formValues['data_forward_url']
                : (credentials?.data_forward_url ?? '')
            }
            onChange={(e) => handleChange('data_forward_url', e.target.value)}
            placeholder="http://backend:8000/api/v1/data-forward/invoice"
            className={inputClassName.replace('pr-10', '')}
          />
        </div>
      </div>

      {/* Submit Buttons */}
      <div className="flex items-center gap-3 pt-4">
        <button
          type="submit"
          disabled={saving || !dirty}
          className="inline-flex items-center gap-2 rounded-md bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <Save className="h-4 w-4" />
          {saving ? 'Guardando...' : 'Guardar'}
        </button>
        {onApplyWorkflow && (
          <button
            type="button"
            onClick={onApplyWorkflow}
            disabled={applyingWorkflow}
            className="inline-flex items-center gap-2 rounded-md border border-amber-500 bg-amber-50 px-4 py-2 text-sm font-medium text-amber-700 hover:bg-amber-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Zap className="h-4 w-4" />
            {applyingWorkflow ? 'Aplicando...' : 'Aplicar al Workflow'}
          </button>
        )}
      </div>

      {/* Test Database Button */}
      {onTestDb && (
        <div className="pt-4">
          <button
            type="button"
            onClick={onTestDb}
            disabled={testingDb}
            className="inline-flex items-center gap-2 rounded-md border border-teal-500 bg-teal-50 px-4 py-2 text-sm font-medium text-teal-700 hover:bg-teal-100 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {testingDb ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Database className="h-4 w-4" />
            )}
            {testingDb ? 'Probando...' : 'Probar Base de Datos'}
          </button>
          {testDbResult && (
            <div
              className={`mt-3 flex items-start gap-2 rounded-md p-3 text-sm ${
                testDbResult.success
                  ? 'bg-green-50 text-green-700 border border-green-200'
                  : 'bg-red-50 text-red-700 border border-red-200'
              }`}
            >
              {testDbResult.success ? (
                <CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" />
              ) : (
                <XCircle className="h-4 w-4 mt-0.5 shrink-0" />
              )}
              <span>{testDbResult.message}</span>
            </div>
          )}
        </div>
      )}
    </form>
  );
}
