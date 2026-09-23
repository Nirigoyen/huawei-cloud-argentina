import { create } from 'zustand';
import { chatbotApi } from '../api/chatbot';
import type { ChatMessage } from '../types/chatbot';
import type { ApiError } from '../types/api';

interface ChatbotState {
  messages: ChatMessage[];
  loading: boolean;
  error: string | null;
  sendMessage: (question: string) => Promise<void>;
  clearHistory: () => void;
}

let messageCounter = 0;

export const useChatbotStore = create<ChatbotState>((set) => ({
  messages: [],
  loading: false,
  error: null,

  sendMessage: async (question) => {
    // Add user message immediately
    const userMessage: ChatMessage = {
      id: `msg-${++messageCounter}`,
      role: 'user',
      content: question,
      timestamp: new Date(),
    };
    set((state) => ({
      messages: [...state.messages, userMessage],
      loading: true,
      error: null,
    }));

    try {
      const data = await chatbotApi.query(question);
      const assistantMessage: ChatMessage = {
        id: `msg-${++messageCounter}`,
        role: 'assistant',
        content: data.response,
        intent: data.intent,
        timestamp: new Date(),
      };
      set((state) => ({
        messages: [...state.messages, assistantMessage],
        loading: false,
      }));
    } catch (err) {
      const apiErr = err as ApiError;
      const errorMessage: ChatMessage = {
        id: `msg-${++messageCounter}`,
        role: 'assistant',
        content: `Error: ${apiErr.detail || 'No se pudo procesar la consulta.'}`,
        timestamp: new Date(),
      };
      set((state) => ({
        messages: [...state.messages, errorMessage],
        loading: false,
        error: apiErr.detail,
      }));
    }
  },

  clearHistory: () => {
    set({ messages: [], error: null });
  },
}));
