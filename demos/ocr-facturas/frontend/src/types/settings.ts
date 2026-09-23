// Application settings / credentials
export interface AppSettings {
  huawei_iam_username: string | null;
  huawei_iam_password: string | null;
  huawei_project_id: string | null;
  dify_api_key: string | null;
  dify_web_url: string | null;
  dify_llm_api_key: string | null;
  dify_llm_base_url: string | null;
  dify_llm_model_name: string | null;
  dify_llm_prompt?: string | null;
  maas_api_key: string | null;
  maas_base_url: string | null;
  maas_model_name: string | null;
  // Destination Database
  destination_db_type: string | null;
  destination_db_host: string | null;
  destination_db_port: string | null;
  destination_db_name: string | null;
  destination_db_username: string | null;
  destination_db_password: string | null;
  destination_db_table: string | null;
  data_forward_enabled: boolean | null;
  data_forward_url: string | null;
}

// Credential update request
export interface CredentialUpdate {
  huawei_iam_username?: string;
  huawei_iam_password?: string;
  huawei_project_id?: string;
  dify_api_key?: string;
  dify_web_url?: string;
  dify_llm_api_key?: string;
  dify_llm_base_url?: string;
  dify_llm_model_name?: string;
  dify_llm_prompt?: string;
  maas_api_key?: string;
  maas_base_url?: string;
  maas_model_name?: string;
  // Destination Database
  destination_db_type?: string;
  destination_db_host?: string;
  destination_db_port?: string;
  destination_db_name?: string;
  destination_db_username?: string;
  destination_db_password?: string;
  destination_db_table?: string;
  data_forward_enabled?: boolean;
  data_forward_url?: string;
}

// Dify model info
export interface DifyModelInfo {
  id: string;
  name: string;
  type: string;
  status: string;
}

// Dify models response
export interface DifyModelsResponse {
  models: DifyModelInfo[];
}

// Dify default prompt response
export interface DifyDefaultPromptResponse {
  prompt: string;
}

// Service names for connection testing
export type ServiceName = 'huawei_iam' | 'dify' | 'maas';

// Connection test request
export interface ConnectionTestRequest {
  service: ServiceName;
}

// Connection test result
export interface ConnectionTestResult {
  success: boolean;
  message: string;
  latency_ms: number | null;
}

// Connection test state for UI
export interface ConnectionTestState {
  status: 'idle' | 'testing' | 'success' | 'failure';
  message: string | null;
  latency_ms: number | null;
}
