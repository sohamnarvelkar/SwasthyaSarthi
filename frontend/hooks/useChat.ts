/**
 * useChat Hook
 * Manages chat state and interactions with the backend
 */

import { useState, useCallback, useRef } from 'react';
import { sendChatMessage, ChatMessage, ChatResponse } from '@/services/api';

export interface UseChatOptions {
  userId?: string;
  userEmail?: string;
  sessionId?: string;
  onResponse?: (response: ChatResponse) => void;
}

export interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
  setMessages: (messages: ChatMessage[]) => void;
}

export function useChat(options: UseChatOptions = {}): UseChatReturn {
  const {
    userId = 'default',
    userEmail = 'user@example.com',
    sessionId,
    onResponse,
  } = options;

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const messageIdRef = useRef(0);

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || isLoading) return;

    // Add user message to chat
    const userMessage: ChatMessage = {
      id: `msg-${++messageIdRef.current}`,
      role: 'user',
      content: content.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await sendChatMessage(
        content,
        userId,
        userEmail,
        undefined,
        sessionId
      );

      // Add assistant message to chat
      const assistantMessage: ChatMessage = {
        id: `msg-${++messageIdRef.current}`,
        role: 'assistant',
        content: response.text,
        language: response.language,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, assistantMessage]);
      onResponse?.(response);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to send message';
      setError(errorMessage);
      
      // Add error message to chat
      const errorMsg: ChatMessage = {
        id: `msg-${++messageIdRef.current}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  }, [userId, userEmail, sessionId, isLoading, onResponse]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearMessages,
    setMessages,
  };
}
