// Type declarations for Web Speech API (must be at top)
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}

interface SpeechRecognitionResultList {
  length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: SpeechRecognitionEvent) => void) | null;
  onerror: ((event: SpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  onstart: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

declare global {
  interface Window {
    SpeechRecognition: new () => SpeechRecognition;
    webkitSpeechRecognition: new () => SpeechRecognition;
  }
}

/**
 * useVoiceAgent Hook
 * Handles continuous voice conversation using Web Speech API
 * Flow: listen → send → receive → speak → listen
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import { sendVoiceMessage, getAudioUrl, VoiceResponse } from '@/services/api';

export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking' | 'error';

export interface UseVoiceAgentOptions {
  userId?: string;
  userEmail?: string;
  sessionId?: string;
  onMessage?: (text: string, response: VoiceResponse) => void;
  onStateChange?: (state: VoiceState) => void;
  onLanguageChange?: (language: string) => void;
}

export interface UseVoiceAgentReturn {
  state: VoiceState;
  transcript: string;
  lastResponse: VoiceResponse | null;
  error: string | null;
  isActive: boolean;
  startListening: () => void;
  stopListening: () => void;
  toggleVoice: () => void;
  detectedLanguage: string;
}

export function useVoiceAgent(options: UseVoiceAgentOptions = {}): UseVoiceAgentReturn {
  const {
    userId = 'default',
    userEmail = 'user@example.com',
    sessionId,
    onMessage,
    onStateChange,
    onLanguageChange,
  } = options;

  const [state, setState] = useState<VoiceState>('idle');
  const [transcript, setTranscript] = useState('');
  const [lastResponse, setLastResponse] = useState<VoiceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [detectedLanguage, setDetectedLanguage] = useState('English');
  const [isActive, setIsActive] = useState(false);

  // Use refs to avoid stale closures
  const isActiveRef = useRef(false);
  const isProcessingRef = useRef(false);
  const optionsRef = useRef({ userId, userEmail, sessionId, onMessage, onStateChange, onLanguageChange });
  const recognitionRef = useRef<SpeechRecognition | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  
  // Keep options ref updated
  useEffect(() => {
    optionsRef.current = { userId, userEmail, sessionId, onMessage, onStateChange, onLanguageChange };
  }, [userId, userEmail, sessionId, onMessage, onStateChange, onLanguageChange]);

  // Keep isActiveRef in sync with isActive state
  useEffect(() => {
    isActiveRef.current = isActive;
  }, [isActive]);

  // Detect language from transcript
  const detectLanguage = useCallback((text: string): string => {
    // Check for Devanagari script (Hindi/Marathi)
    const devanagariRegex = /[\u0900-\u097F]/;
    if (devanagariRegex.test(text)) {
      // Simple keyword-based detection
      const hindiWords = ['है', 'हैं', 'मैं', 'मुझे', 'आप', 'क्या'];
      const marathiWords = ['आहे', 'मी', 'मला', 'तुम्ही', 'काय'];
      
      const hindiCount = hindiWords.filter(w => text.includes(w)).length;
      const marathiCount = marathiWords.filter(w => text.includes(w)).length;
      
      if (marathiCount > hindiCount) {
        return 'Marathi';
      }
      return 'Hindi';
    }
    return 'English';
  }, []);

  // Set recognition language based on detected language
  const updateRecognitionLanguage = useCallback((language: string) => {
    if (!recognitionRef.current) return;
    
    const langMap: Record<string, string> = {
      'English': 'en-US',
      'Hindi': 'hi-IN',
      'Marathi': 'mr-IN',
    };
    
    recognitionRef.current.lang = langMap[language] || 'en-US';
    setDetectedLanguage(language);
    optionsRef.current.onLanguageChange?.(language);
  }, []);

  // Process voice input - send to backend
  const processVoiceInput = useCallback(async (text: string) => {
    if (isProcessingRef.current || !text.trim()) return;
    
    isProcessingRef.current = true;
    setState('processing');
    optionsRef.current.onStateChange?.('processing');

    try {
      // Detect language
      const lang = detectLanguage(text);
      updateRecognitionLanguage(lang);

      // Stop recognition while processing
      try {
        recognitionRef.current?.stop();
      } catch (e) {
        // Ignore
      }

      // Send to backend
      const response = await sendVoiceMessage(
        text,
        optionsRef.current.userId,
        optionsRef.current.userEmail,
        lang,
        optionsRef.current.sessionId
      );

      setLastResponse(response);
      
      // Play audio if available
      if (response.audio_url) {
        setState('speaking');
        optionsRef.current.onStateChange?.('speaking');
        
        const audioUrl = getAudioUrl(response.audio_url);
        
        if (audioRef.current) {
          audioRef.current.src = audioUrl;
          await audioRef.current.play();
        }
      }

      // Notify callback
      optionsRef.current.onMessage?.(text, response);

      // If voice is still active, restart listening
      if (isActiveRef.current) {
        setState('listening');
        optionsRef.current.onStateChange?.('listening');
        
        // Small delay before restarting recognition
        setTimeout(() => {
          try {
            recognitionRef.current?.start();
          } catch (e) {
            console.log('Failed to restart recognition:', e);
          }
          isProcessingRef.current = false;
        }, 500);
      } else {
        isProcessingRef.current = false;
        setState('idle');
      }
    } catch (err) {
      console.error('Voice processing error:', err);
      setError(err instanceof Error ? err.message : 'Unknown error');
      setState('error');
      isProcessingRef.current = false;
      
      // Restart listening after error if still active
      if (isActiveRef.current) {
        setTimeout(() => {
          restartListening();
        }, 1000);
      }
    }
  }, [detectLanguage, updateRecognitionLanguage]);

  // Restart listening
  const restartListening = useCallback(() => {
    if (!recognitionRef.current || isProcessingRef.current) return;
    
    try {
      recognitionRef.current.start();
      setState('listening');
      optionsRef.current.onStateChange?.('listening');
      setError(null);
    } catch (e) {
      console.log('Failed to start recognition:', e);
    }
  }, []);

  // Initialize speech recognition (only once)
  useEffect(() => {
    if (typeof window === 'undefined') return;

    const SpeechRecognitionAPI = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognitionAPI) {
      setError('Speech recognition not supported in this browser');
      return;
    }

    const recognition = new SpeechRecognitionAPI();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const last = event.results.length - 1;
      const text = event.results[last][0].transcript.trim();
      
      if (text) {
        setTranscript(text);
        // Auto-restart listening for continuous conversation
        processVoiceInput(text);
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      console.error('Speech recognition error:', event.error);
      
      if (event.error === 'no-speech') {
        // No speech detected - continue listening (use ref to get current value)
        if (isActiveRef.current && !isProcessingRef.current) {
          restartListening();
        }
      } else if (event.error !== 'aborted') {
        setError(`Speech error: ${event.error}`);
        setState('error');
      }
    };

    recognition.onend = () => {
      // Restart recognition if still active (use ref to get current value)
      if (isActiveRef.current && !isProcessingRef.current) {
        try {
          recognition.start();
        } catch (e) {
          console.log('Recognition restart failed:', e);
        }
      }
    };

    recognitionRef.current = recognition;

    return () => {
      try {
        recognition.stop();
      } catch (e) {
        // Ignore errors on cleanup
      }
    };
  }, [processVoiceInput, restartListening]);

  // Start voice agent
  const startListening = useCallback(() => {
    if (!recognitionRef.current) {
      setError('Speech recognition not available');
      return;
    }

    setIsActive(true);
    setError(null);
    setTranscript('');
    
    try {
      recognitionRef.current.start();
      setState('listening');
      optionsRef.current.onStateChange?.('listening');
    } catch (e) {
      console.error('Failed to start recognition:', e);
      setError('Failed to start voice recognition');
      setState('error');
    }
  }, []);

  // Stop voice agent
  const stopListening = useCallback(() => {
    setIsActive(false);
    isProcessingRef.current = false;
    
    try {
      recognitionRef.current?.stop();
    } catch (e) {
      // Ignore
    }
    
    // Stop any playing audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    
    setState('idle');
    optionsRef.current.onStateChange?.('idle');
  }, []);

  // Toggle voice agent on/off
  const toggleVoice = useCallback(() => {
    if (isActive) {
      stopListening();
    } else {
      startListening();
    }
  }, [isActive, startListening, stopListening]);

  return {
    state,
    transcript,
    lastResponse,
    error,
    isActive,
    startListening,
    stopListening,
    toggleVoice,
    detectedLanguage,
  };
}

export {};
