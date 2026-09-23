import type { ReactNode } from 'react';
import type { ChatMessage as ChatMessageType } from '../../types/chatbot';
import { User, Bot } from 'lucide-react';

interface ChatMessageProps {
  message: ChatMessageType;
}

/** Lightweight inline markdown renderer for chatbot responses.
 *  Handles **bold**, *italic*, `code`, and bullet lists (- ). */
function renderMarkdown(text: string): ReactNode {
  const lines = text.split('\n');
  return lines.map((line, i) => {
    const bullet = line.trimStart().startsWith('- ');
    const content = bullet ? line.trimStart().slice(2) : line;
    const rendered = renderInline(content);
    return (
      <span key={i} className="block">
        {bullet && <span className="mr-1">•</span>}
        {rendered}
      </span>
    );
  });
}

function renderInline(text: string): ReactNode[] {
  // Split on **bold**, *italic*, `code` patterns
  const parts: ReactNode[] = [];
  const regex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    const token = match[0];
    if (token.startsWith('**')) {
      parts.push(<strong key={key++}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith('`')) {
      parts.push(
        <code key={key++} className="rounded bg-gray-100 px-1 py-0.5 text-xs">
          {token.slice(1, -1)}
        </code>,
      );
    } else {
      parts.push(<em key={key++}>{token.slice(1, -1)}</em>);
    }
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < text.length) {
    parts.push(text.slice(lastIndex));
  }
  return parts;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-100 text-primary-600">
          <Bot className="h-4 w-4" />
        </div>
      )}
      <div
        className={`max-w-[75%] rounded-lg px-4 py-2.5 text-sm ${
          isUser
            ? 'bg-primary-600 text-white'
            : 'bg-white text-gray-900 border border-gray-200 shadow-sm'
        }`}
      >
        <div className="whitespace-pre-wrap">
          {isUser ? message.content : renderMarkdown(message.content)}
        </div>
        {message.intent && !isUser && (
          <p className="mt-1 text-xs text-gray-400">Intento: {message.intent}</p>
        )}
      </div>
      {isUser && (
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-200 text-gray-600">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  );
}
