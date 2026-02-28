'use client';

import React from 'react';
import { Globe } from 'lucide-react';

interface LanguageIndicatorProps {
  language: string;
  onChange?: (language: string) => void;
}

const LANGUAGES = [
  { code: 'English', name: 'English', flag: '🇬🇧' },
  { code: 'Hindi', name: 'हिंदी', flag: '🇮🇳' },
  { code: 'Marathi', name: 'मराठी', flag: '🇮🇳' },
];

export function LanguageIndicator({ language, onChange }: LanguageIndicatorProps) {
  const currentLang = LANGUAGES.find(l => l.code === language) || LANGUAGES[0];

  return (
    <div className="relative inline-block">
      <button
        className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-lg text-sm font-medium transition-colors"
        onClick={() => {
          if (onChange) {
            const currentIndex = LANGUAGES.findIndex(l => l.code === language);
            const nextIndex = (currentIndex + 1) % LANGUAGES.length;
            onChange(LANGUAGES[nextIndex].code);
          }
        }}
      >
        <Globe size={16} />
        <span>{currentLang.flag}</span>
        <span>{currentLang.name}</span>
      </button>
    </div>
  );
}
