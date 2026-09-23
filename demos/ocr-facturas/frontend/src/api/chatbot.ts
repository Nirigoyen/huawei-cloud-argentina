import apiClient from './apiClient';
import type { ChatbotResponse } from '../types/chatbot';

export const chatbotApi = {
  /**
   * Send a natural-language query to the chatbot
   */
  query: async (question: string): Promise<ChatbotResponse> => {
    const response = await apiClient.post<ChatbotResponse>('/chatbot/query', {
      question,
    });
    return response.data;
  },
};
