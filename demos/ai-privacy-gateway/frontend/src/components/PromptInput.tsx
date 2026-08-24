import { useState } from 'react';
import type { ProcessResponse, PipelineStep } from '../types';
import { processPrompt } from '../services/api';
import { PipelineCard } from './PipelineCard';

const STEPS_CONFIG: {
  step: number;
  title: string;
  highlightPlaceholders?: boolean;
  renderMarkdown?: boolean;
}[] = [
  { step: 1, title: 'Original Prompt' },
  { step: 2, title: 'Anonymized Prompt', highlightPlaceholders: true },
  { step: 3, title: 'Raw LLM Response', highlightPlaceholders: true, renderMarkdown: true },
  { step: 4, title: 'Reconstructed Response', renderMarkdown: true },
];

const STEP_KEYS: (keyof ProcessResponse)[] = [
  'original_prompt',
  'anonymized_prompt',
  'llm_raw_response',
  'final_deanonymized_response',
];

const STEP_DELAYS = [0, 300, 600, 900];

export function PromptInput() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [visibleSteps, setVisibleSteps] = useState<number>(0);
  const [steps, setSteps] = useState<PipelineStep[]>([]);

  const handleSubmit = async () => {
    if (!prompt.trim()) return;

    setLoading(true);
    setError(null);
    setVisibleSteps(0);
    setSteps([]);

    try {
      const response: ProcessResponse = await processPrompt(prompt);

      const newSteps: PipelineStep[] = STEPS_CONFIG.map((config, index) => ({
        step: config.step,
        title: config.title,
        content: response[STEP_KEYS[index]],
        highlightPlaceholders: config.highlightPlaceholders,
        renderMarkdown: config.renderMarkdown,
      }));

      setSteps(newSteps);

      STEP_DELAYS.forEach((delay, index) => {
        setTimeout(() => {
          setVisibleSteps((prev) => Math.max(prev, index + 1));
        }, delay);
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6">
      <div className="bg-white rounded-lg shadow-sm border border-huawei-gray-200 overflow-hidden">
        <div className="flex items-center gap-2 px-5 py-3 bg-huawei-gray-50 border-b border-huawei-gray-200">
          <div className="flex items-center justify-center w-6 h-6 rounded bg-huawei-blue text-white">
            <svg
              className="w-3.5 h-3.5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931z"
              />
            </svg>
          </div>
          <span className="text-sm font-medium text-huawei-gray-700">Enter your prompt</span>
        </div>
        <div className="p-5">
          <textarea
            id="prompt-input"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            rows={4}
            className="w-full rounded-md border border-huawei-gray-200 px-4 py-3 text-sm text-huawei-gray-800 placeholder-huawei-gray-300 focus:border-huawei-blue focus:ring-1 focus:ring-huawei-blue outline-none transition resize-y bg-huawei-gray-50"
            placeholder="e.g. My name is Nicolas Garcia, my email is nico@example.com and my phone is +1 555 123 4567..."
            disabled={loading}
          />
          <div className="mt-4 flex items-center gap-4">
            <button
              onClick={handleSubmit}
              disabled={loading || !prompt.trim()}
              className="inline-flex items-center gap-2 rounded-md bg-huawei-blue px-5 py-2 text-sm font-medium text-white shadow-sm hover:bg-huawei-blue-dark focus:outline-none focus:ring-2 focus:ring-huawei-blue/50 disabled:opacity-50 disabled:cursor-not-allowed transition"
            >
              {loading && (
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                  />
                </svg>
              )}
              {loading ? 'Processing...' : 'Process & Send to LLM'}
            </button>
            {error && <span className="text-sm text-red-500 font-medium">{error}</span>}
          </div>
        </div>
      </div>

      {steps.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {steps.map((step, index) => (
            <div
              key={step.step}
              className={`transition-all duration-300 ${
                index < visibleSteps
                  ? 'opacity-100 translate-y-0'
                  : 'opacity-0 translate-y-4 pointer-events-none'
              }`}
              style={{
                transitionDelay: `${STEP_DELAYS[index]}ms`,
              }}
            >
              <PipelineCard
                step={step.step}
                title={step.title}
                content={step.content}
                highlightPlaceholders={step.highlightPlaceholders}
                renderMarkdown={step.renderMarkdown}
              />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
