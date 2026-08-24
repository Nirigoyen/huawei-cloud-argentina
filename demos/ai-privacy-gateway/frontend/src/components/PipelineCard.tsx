import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';

interface PipelineCardProps {
  step: number;
  title: string;
  content: string;
  highlightPlaceholders?: boolean;
  renderMarkdown?: boolean;
}

const STEP_COLORS: Record<number, { border: string; badge: string; icon: string }> = {
  1: { border: 'border-blue-300', badge: 'bg-blue-100 text-blue-700', icon: '📝' },
  2: { border: 'border-amber-300', badge: 'bg-amber-100 text-amber-700', icon: '🔒' },
  3: { border: 'border-purple-300', badge: 'bg-purple-100 text-purple-700', icon: '🤖' },
  4: { border: 'border-emerald-300', badge: 'bg-emerald-100 text-emerald-700', icon: '✅' },
};

const PLACEHOLDER_REGEX = /(<[A-Z_]+_\d+>)/g;
const IS_PLACEHOLDER = /^<[A-Z_]+_\d+>$/;

const MD_COMPONENTS = {
  p: ({ children }: { children?: React.ReactNode }) => <p className="mb-2 last:mb-0">{children}</p>,
  strong: ({ children }: { children?: React.ReactNode }) => (
    <strong className="font-semibold text-gray-900">{children}</strong>
  ),
  em: ({ children }: { children?: React.ReactNode }) => <em className="italic">{children}</em>,
  ul: ({ children }: { children?: React.ReactNode }) => (
    <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>
  ),
  ol: ({ children }: { children?: React.ReactNode }) => (
    <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>
  ),
  li: ({ children }: { children?: React.ReactNode }) => <li>{children}</li>,
  h1: ({ children }: { children?: React.ReactNode }) => (
    <h1 className="text-base font-bold mb-2 text-gray-900">{children}</h1>
  ),
  h2: ({ children }: { children?: React.ReactNode }) => (
    <h2 className="text-sm font-bold mb-1.5 text-gray-900">{children}</h2>
  ),
  h3: ({ children }: { children?: React.ReactNode }) => (
    <h3 className="text-sm font-semibold mb-1 text-gray-900">{children}</h3>
  ),
  code: ({ children }: { children?: React.ReactNode }) => (
    <code className="bg-gray-200 px-1 py-0.5 rounded text-xs">{children}</code>
  ),
};

function HighlightedContent({ content }: { content: string }) {
  const parts = useMemo(() => {
    const segments = content.split(PLACEHOLDER_REGEX);
    return segments.map((segment, index) => {
      if (IS_PLACEHOLDER.test(segment)) {
        return (
          <span
            key={index}
            className="inline-flex items-center rounded-md bg-amber-100 px-1.5 py-0.5 text-xs font-bold text-amber-800 border border-amber-300 mx-0.5"
          >
            {segment}
          </span>
        );
      }
      return <span key={index}>{segment}</span>;
    });
  }, [content]);

  return <>{parts}</>;
}

function MarkdownWithPlaceholders({ content }: { content: string }) {
  const prepared = useMemo(() => {
    return content.replace(PLACEHOLDER_REGEX, (match) => {
      return `**⟨${match.slice(1, -1)}⟩**`;
    });
  }, [content]);

  const components = useMemo(
    () => ({
      ...MD_COMPONENTS,
      strong: ({ children }: { children?: React.ReactNode }) => {
        const raw = String(children);
        const match = raw.match(/^⟨(.+)⟩$/);
        if (match) {
          return (
            <span className="inline-flex items-center rounded-md bg-amber-100 px-1.5 py-0.5 text-xs font-bold text-amber-800 border border-amber-300 mx-0.5">
              {`<${match[1]}>`}
            </span>
          );
        }
        return <strong className="font-semibold text-gray-900">{children}</strong>;
      },
    }),
    [],
  );

  return <ReactMarkdown components={components}>{prepared}</ReactMarkdown>;
}

export function PipelineCard({
  step,
  title,
  content,
  highlightPlaceholders,
  renderMarkdown,
}: PipelineCardProps) {
  const colors = STEP_COLORS[step] || STEP_COLORS[1];

  return (
    <div
      className={`rounded-xl border-l-4 ${colors.border} bg-white shadow-sm p-5 animate-fade-in-up`}
    >
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">{colors.icon}</span>
        <span
          className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${colors.badge}`}
        >
          Step {step}
        </span>
        <h3 className="text-sm font-semibold text-gray-800">{title}</h3>
      </div>
      <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 text-sm text-gray-700 break-words leading-relaxed max-h-64 overflow-y-auto">
        {renderMarkdown && highlightPlaceholders ? (
          <MarkdownWithPlaceholders content={content} />
        ) : renderMarkdown ? (
          <ReactMarkdown components={MD_COMPONENTS}>{content}</ReactMarkdown>
        ) : highlightPlaceholders ? (
          <HighlightedContent content={content} />
        ) : (
          <pre className="whitespace-pre-wrap font-sans m-0">{content}</pre>
        )}
      </div>
    </div>
  );
}
