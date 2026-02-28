'use client';

import React from 'react';
import { Mic, MicOff, Loader2 } from 'lucide-react';
import { VoiceState } from '@/hooks/useVoiceAgent';

interface VoiceAgentButtonProps {
  isActive: boolean;
  state: VoiceState;
  onToggle: () => void;
  disabled?: boolean;
}

export function VoiceAgentButton({ 
  isActive, 
  state, 
  onToggle, 
  disabled = false 
}: VoiceAgentButtonProps) {
  const getButtonContent = () => {
    switch (state) {
      case 'listening':
        return (
          <div className="flex items-center gap-2">
            <div className="relative">
              <Mic size={20} className="text-red-500" />
              <span className="absolute -top-1 -right-1 w-3 h-3 bg-red-500 rounded-full animate-ping" />
            </div>
            <span className="text-sm font-medium">Listening...</span>
          </div>
        );
      case 'processing':
        return (
          <div className="flex items-center gap-2">
            <Loader2 size={20} className="animate-spin text-blue-500" />
            <span className="text-sm font-medium">Processing...</span>
          </div>
        );
      case 'speaking':
        return (
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 bg-green-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium">Speaking...</span>
          </div>
        );
      case 'error':
        return (
          <div className="flex items-center gap-2">
            <MicOff size={20} className="text-red-500" />
            <span className="text-sm font-medium">Error - Tap to retry</span>
          </div>
        );
      default:
        return (
          <div className="flex items-center gap-2">
            <Mic size={20} />
            <span className="text-sm font-medium">Start Voice Agent</span>
          </div>
        );
    }
  };

  const getButtonStyle = () => {
    if (state === 'error') {
      return 'bg-red-100 dark:bg-red-900/30 border-red-300 dark:border-red-700 hover:bg-red-200 dark:hover:bg-red-900/50';
    }
    if (isActive) {
      return 'bg-healthcare border-healthcare-dark text-white hover:bg-healthcare-dark';
    }
    return 'bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-600 hover:border-primary-500 dark:hover:border-primary-400';
  };

  return (
    <button
      onClick={onToggle}
      disabled={disabled}
      className={`
        flex items-center justify-center px-6 py-3 
        rounded-full border-2 font-medium transition-all duration-200
        ${getButtonStyle()}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer shadow-md hover:shadow-lg'}
        min-w-[180px]
      `}
    >
      {getButtonContent()}
    </button>
  );
}
