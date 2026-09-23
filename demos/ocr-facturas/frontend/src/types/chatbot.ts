// Chatbot query request
export interface ChatbotQuery {
  question: string;
}

// Chatbot response
export interface ChatbotResponse {
  response: string;
  intent: string | null;
  query_log_id: string;
}

// Chat message for UI
export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  intent?: string | null;
  timestamp: Date;
}
