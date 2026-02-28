'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Pill, FileText, Clock, Search, Settings, UserRound } from 'lucide-react';
import { MessageBubble } from './MessageBubble';
import { VoiceAgentButton } from './VoiceAgentButton';
import { VoiceVisualizer } from './VoiceVisualizer';
import { LanguageIndicator } from './LanguageIndicator';
import { ChatMessage } from '@/services/api';
import { VoiceState } from '@/hooks/useVoiceAgent';

interface ChatWindowProps {
  messages: ChatMessage[];
  isLoading: boolean;
  onSendMessage: (message: string) => void;
  onSpeak?: (text: string, language?: string) => void;
  isVoiceMode: boolean;
  voiceState: VoiceState;
  voiceTranscript?: string;
  voiceLanguage?: string;
  onToggleVoice: () => void;
  currentLanguage: string;
  onLanguageChange: (language: string) => void;
  onOpenTools?: (tool: string) => void;
}

export function ChatWindow({
  messages,
  isLoading,
  onSendMessage,
  onSpeak,
  isVoiceMode,
  voiceState,
  voiceTranscript,
  voiceLanguage,
  onToggleVoice,
  currentLanguage,
  onLanguageChange,
  onOpenTools,
}: ChatWindowProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input on mount
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleToolClick = (tool: string) => {
    // Tools should call APIs directly instead of sending as chat messages
    // This is handled by the parent component through onOpenTools
    onOpenTools?.(tool);
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-white dark:bg-slate-900">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 dark:border-slate-700">
        <div>
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
            {isVoiceMode ? '🎙️ Voice Conversation' : '💬 Chat'}
          </h2>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            SwasthyaSarthi AI Assistant
          </p>
        </div>
        <div className="flex items-center gap-4">
          <LanguageIndicator
            language={currentLanguage}
            onChange={onLanguageChange}
          />
        </div>
      </div>

      {/* Tools Toolbar */}
      <div className="flex items-center gap-2 px-6 py-2 border-b border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 overflow-x-auto">
        <span className="text-xs font-medium text-slate-500 dark:text-slate-400 mr-2">
          Tools:
        </span>
        
        <button
          onClick={() => handleToolClick('medicines')}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg hover:bg-primary-50 dark:hover:bg-primary-900/30 text-slate-700 dark:text-slate-300 transition-colors"
          title="Browse Medicines"
        >
          <Pill size={14} className="text-primary-500" />
          Medicines
        </button>

        <button
          onClick={() => handleToolClick('prescription')}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/30 text-slate-700 dark:text-slate-300 transition-colors"
          title="Upload Prescription"
        >
          <FileText size={14} className="text-blue-500" />
          Prescription
        </button>

        <button
          onClick={() => handleToolClick('orders')}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg hover:bg-green-50 dark:hover:bg-green-900/30 text-slate-700 dark:text-slate-300 transition-colors"
          title="Order History"
        >
          <Search size={14} className="text-green-500" />
          My Orders
        </button>

        <button
          onClick={() => handleToolClick('refills')}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg hover:bg-orange-50 dark:hover:bg-orange-900/30 text-slate-700 dark:text-slate-300 transition-colors"
          title="Refill Reminders"
        >
          <Clock size={14} className="text-orange-500" />
          Refills
        </button>

        <button
          onClick={() => handleToolClick('profile')}
          className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-lg hover:bg-purple-50 dark:hover:bg-purple-900/30 text-slate-700 dark:text-slate-300 transition-colors"
          title="My Profile"
        >
          <UserRound size={14} className="text-purple-500" />
          Profile
        </button>
      </div>

      {/* Messages area */}
      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="text-6xl mb-4">🩺</div>
            <h3 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
              Welcome to SwasthyaSarthi
            </h3>
            <p className="text-slate-500 dark:text-slate-400 max-w-md">
              Your friendly AI pharmacy assistant. Type a message or click the
              microphone to start a voice conversation.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                message={message}
                onSpeak={onSpeak}
              />
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="flex items-center gap-2 px-4 py-2 bg-slate-100 dark:bg-slate-800 rounded-2xl rounded-bl-sm">
                  <div className="flex gap-1">
                    <span className="w-2 h-2 bg-slate-400 rounded-full typing-dot" />
                    <span className="w-2 h-2 bg-slate-400 rounded-full typing-dot" />
                    <span className="w-2 h-2 bg-slate-400 rounded-full typing-dot" />
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Voice mode visualization */}
      {isVoiceMode && (
        <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50">
          <VoiceVisualizer
            state={voiceState}
            transcript={voiceTranscript}
            language={voiceLanguage || currentLanguage}
          />
        </div>
      )}

      {/* Input area */}
      <div className="px-6 py-4 border-t border-slate-200 dark:border-slate-700">
        <form onSubmit={handleSubmit} className="flex items-end gap-3">
          {/* Voice toggle button */}
          <VoiceAgentButton
            isActive={isVoiceMode}
            state={voiceState}
            onToggle={onToggleVoice}
            disabled={isLoading}
          />

          {/* Text input */}
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Type your message..."
              className="w-full px-4 py-3 pr-12 bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400 text-slate-900 dark:text-white placeholder-slate-400"
              rows={1}
              disabled={isLoading}
            />
          </div>

          {/* Send button */}
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="p-3 bg-primary-500 hover:bg-primary-600 disabled:bg-slate-300 dark:disabled:bg-slate-700 text-white rounded-xl transition-colors"
          >
            {isLoading ? (
              <Loader2 size={20} className="animate-spin" />
            ) : (
              <Send size={20} />
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
