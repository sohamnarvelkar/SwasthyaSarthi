'use client';

import React from 'react';
import { Bot, User, Volume2 } from 'lucide-react';
import { ChatMessage } from '@/services/api';

interface MessageBubbleProps {
  message: ChatMessage;
  onSpeak?: (text: string, language?: string) => void;
}

export function MessageBubble({ message, onSpeak }: MessageBubbleProps) {
  const isUser = message.role === 'user';

  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString([], { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const handleSpeak = () => {
    if (onSpeak && message.role === 'assistant') {
      onSpeak(message.content, message.language);
    }
  };

  return (
    <div
      className={`flex w-full ${isUser ? 'justify-end' : 'justify-start'} mb-4 message-enter`}
    >
      <div
        className={`flex max-w-[80%] ${isUser ? 'flex-row-reverse' : 'flex-row'} items-start gap-2`}
      >
        {/* Avatar */}
        <div
          className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
            isUser
              ? 'bg-primary-500 text-white'
              : 'bg-healthcare text-white'
          }`}
        >
          {isUser ? <User size={16} /> : <Bot size={16} />}
        </div>

        {/* Message bubble */}
        <div
          className={`flex flex-col ${
            isUser ? 'items-end' : 'items-start'
          }`}
        >
          <div
            className={`px-4 py-2 rounded-2xl ${
              isUser
                ? 'bg-primary-500 text-white rounded-br-sm'
                : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-bl-sm'
            }`}
          >
            <p className="text-sm whitespace-pre-wrap">{message.content}</p>
          </div>

          {/* Message metadata */}
          <div
            className={`flex items-center gap-2 mt-1 text-xs text-slate-500 ${
              isUser ? 'flex-row-reverse' : 'flex-row'
            }`}
          >
            <span>{formatTime(message.timestamp)}</span>
            {message.language && (
              <span className="px-1.5 py-0.5 bg-slate-200 dark:bg-slate-700 rounded text-xs">
                {message.language}
              </span>
            )}
            {!isUser && onSpeak && (
              <button
                onClick={handleSpeak}
                className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition-colors"
                title="Speak message"
              >
                <Volume2 size={14} />
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
