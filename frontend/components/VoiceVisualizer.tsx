'use client';

import React from 'react';
import { VoiceState } from '@/hooks/useVoiceAgent';

interface VoiceVisualizerProps {
  state: VoiceState;
  transcript?: string;
  language?: string;
}

export function VoiceVisualizer({ state, transcript, language }: VoiceVisualizerProps) {
  const isActive = state !== 'idle' && state !== 'error';

  return (
    <div className="flex flex-col items-center justify-center p-6">
      {/* Main visualizer */}
      <div className="relative mb-4">
        {state === 'listening' && (
          <div className="flex items-center justify-center gap-1">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="w-2 bg-red-500 rounded-full animate-pulse"
                style={{
                  height: `${20 + Math.random() * 30}px`,
                  animationDelay: `${i * 0.1}s`,
                }}
              />
            ))}
          </div>
        )}

        {state === 'processing' && (
          <div className="flex items-center justify-center gap-2">
            <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        )}

        {state === 'speaking' && (
          <div className="flex items-center justify-center gap-1">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="w-3 bg-green-500 rounded-full voice-pulse"
                style={{
                  height: `${30 + Math.random() * 20}px`,
                  animationDelay: `${i * 0.15}s`,
                }}
              />
            ))}
          </div>
        )}

        {state === 'idle' && (
          <div className="w-16 h-16 border-4 border-slate-300 dark:border-slate-600 rounded-full flex items-center justify-center">
            <div className="w-3 h-3 bg-slate-400 rounded-full" />
          </div>
        )}

        {state === 'error' && (
          <div className="w-16 h-16 border-4 border-red-500 rounded-full flex items-center justify-center">
            <div className="w-4 h-4 bg-red-500 rounded-full" />
          </div>
        )}
      </div>

      {/* Status text */}
      <div className="text-center mb-4">
        <p className="text-lg font-medium text-slate-700 dark:text-slate-300">
          {state === 'listening' && '🎤 Listening...'}
          {state === 'processing' && '🤔 Processing...'}
          {state === 'speaking' && '🔊 Speaking...'}
          {state === 'idle' && 'Click to start voice conversation'}
          {state === 'error' && '⚠️ Error occurred'}
        </p>
      </div>

      {/* Live transcript preview */}
      {transcript && isActive && (
        <div className="w-full max-w-md p-4 bg-slate-100 dark:bg-slate-800 rounded-lg">
          <p className="text-sm text-slate-600 dark:text-slate-400 mb-1">You said:</p>
          <p className="text-lg font-medium text-slate-900 dark:text-slate-100">
            {transcript}
          </p>
        </div>
      )}

      {/* Language indicator */}
      {language && isActive && (
        <div className="mt-4 flex items-center gap-2">
          <span className="px-3 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-sm font-medium">
            🌍 {language}
          </span>
        </div>
      )}
    </div>
  );
}
