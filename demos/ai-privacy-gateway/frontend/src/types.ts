export interface ProcessRequest {
  prompt: string;
}

export interface ProcessResponse {
  original_prompt: string;
  anonymized_prompt: string;
  llm_raw_response: string;
  final_deanonymized_response: string;
}

export interface PipelineStep {
  step: number;
  title: string;
  content: string;
  highlightPlaceholders?: boolean;
  renderMarkdown?: boolean;
}
