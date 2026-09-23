import { useEffect, useRef } from 'react';
import { Trash2, MessageSquare } from 'lucide-react';
import { useChatbotStore } from '../stores/useChatbotStore';
import ChatMessage from '../components/chatbot/ChatMessage';
import ChatInput from '../components/chatbot/ChatInput';
import LoadingSpinner from '../components/common/LoadingSpinner';

const SUGGESTED_QUESTIONS = [
  '¿Cuánto gastamos este mes?',
  '¿Quiénes son nuestros principales proveedores?',
  '¿Cuánto IVA pagamos este trimestre?',
  '¿Cuál fue la última factura recibida?',
  '¿Cuántas facturas recibimos este mes?',
  '¿Cuál es el monto promedio de las facturas?',
];

export default function ChatbotPage() {
  const { messages, loading, sendMessage, clearHistory } = useChatbotStore();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="mx-auto flex h-[calc(100vh-10rem)] max-w-3xl flex-col">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 pb-4">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-primary-600" />
          <h2 className="text-lg font-semibold text-gray-900">Consultas sobre Facturas</h2>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearHistory}
            className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-gray-500 hover:bg-gray-100 hover:text-gray-700"
          >
            <Trash2 className="h-3 w-3" />
            Limpiar
          </button>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col items-center justify-center gap-6">
            <div className="rounded-full bg-primary-50 p-6">
              <MessageSquare className="h-10 w-10 text-primary-400" />
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-500">
                Hacé consultas sobre tus facturas en lenguaje natural.
              </p>
              <p className="mt-1 text-xs text-gray-400">Ejemplo: "¿Cuánto gastamos este mes?"</p>
            </div>

            {/* Suggested questions */}
            <div className="flex flex-wrap justify-center gap-2">
              {SUGGESTED_QUESTIONS.map((q) => (
                <button
                  key={q}
                  onClick={() => sendMessage(q)}
                  className="rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs text-gray-600 shadow-sm hover:border-primary-300 hover:bg-primary-50 hover:text-primary-600"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            {loading && <LoadingSpinner size="sm" text="Procesando consulta..." className="py-2" />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 pt-4">
        <ChatInput onSend={sendMessage} disabled={loading} />
      </div>
    </div>
  );
}
