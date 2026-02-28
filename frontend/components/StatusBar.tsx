'use client';

import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  ShieldCheck, 
  ShoppingCart, 
  Mail, 
  ChevronDown, 
  ChevronUp,
  Loader2,
  CheckCircle,
  XCircle
} from 'lucide-react';

export type AgentStatus = 'idle' | 'thinking' | 'checking_safety' | 'creating_order' | 'sending_email' | 'completed' | 'error';

interface StatusStep {
  id: string;
  label: string;
  status: 'pending' | 'in_progress' | 'completed' | 'error';
  details?: string;
}

interface StatusBarProps {
  isVisible: boolean;
  currentStatus: AgentStatus;
  steps?: StatusStep[];
  message?: string;
}

export function StatusBar({ isVisible, currentStatus, steps: initialSteps, message }: StatusBarProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [animatedSteps, setAnimatedSteps] = useState<StatusStep[]>([]);

  // Default steps based on current status
  const defaultSteps: StatusStep[] = [
    { id: 'analyze', label: 'Analyzing your query', status: 'pending' },
    { id: 'reasoning', label: 'AI is reasoning', status: 'pending' },
    { id: 'safety', label: 'Checking safety rules', status: 'pending' },
    { id: 'order', label: 'Creating order', status: 'pending' },
    { id: 'email', label: 'Sending confirmation', status: 'pending' },
  ];

  const steps = initialSteps || animatedSteps;

  useEffect(() => {
    if (!isVisible) {
      setAnimatedSteps([]);
      return;
    }

    // Update steps based on current status
    const stepMapping: Record<AgentStatus, string[]> = {
      idle: [],
      thinking: ['analyze', 'reasoning'],
      checking_safety: ['analyze', 'reasoning', 'safety'],
      creating_order: ['analyze', 'reasoning', 'safety', 'order'],
      sending_email: ['analyze', 'reasoning', 'safety', 'order', 'email'],
      completed: ['analyze', 'reasoning', 'safety', 'order', 'email'],
      error: [],
    };

    const activeSteps = stepMapping[currentStatus];
    
    setAnimatedSteps(defaultSteps.map(step => {
      const stepIndex = activeSteps.indexOf(step.id);
      if (stepIndex === -1) {
        return { ...step, status: 'pending' as const };
      }
      if (stepIndex === activeSteps.length - 1 && currentStatus !== 'completed') {
        return { ...step, status: 'in_progress' as const };
      }
      return { ...step, status: 'completed' as const };
    }));
  }, [isVisible, currentStatus]);

  const getStatusIcon = () => {
    switch (currentStatus) {
      case 'thinking':
        return <Brain size={16} className="text-blue-500 animate-pulse" />;
      case 'checking_safety':
        return <ShieldCheck size={16} className="text-amber-500 animate-pulse" />;
      case 'creating_order':
        return <ShoppingCart size={16} className="text-purple-500 animate-pulse" />;
      case 'sending_email':
        return <Mail size={16} className="text-teal-500 animate-pulse" />;
      case 'completed':
        return <CheckCircle size={16} className="text-green-500" />;
      case 'error':
        return <XCircle size={16} className="text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusMessage = () => {
    switch (currentStatus) {
      case 'thinking':
        return message || 'Analyzing your query and finding the best response...';
      case 'checking_safety':
        return message || 'Verifying medication safety and interactions...';
      case 'creating_order':
        return message || 'Processing your order...';
      case 'sending_email':
        return message || 'Sending confirmation email...';
      case 'completed':
        return message || 'Task completed successfully!';
      case 'error':
        return message || 'An error occurred. Please try again.';
      default:
        return '';
    }
  };

  if (!isVisible || currentStatus === 'idle') {
    return null;
  }

  const isProcessing = ['thinking', 'checking_safety', 'creating_order', 'sending_email'].includes(currentStatus);

  return (
    <div className="w-full bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-lg overflow-hidden">
      {/* Header */}
      <div 
        className="flex items-center justify-between px-4 py-3 bg-slate-50 dark:bg-slate-900/50 cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-3">
          {isProcessing ? (
            <Loader2 size={16} className="text-primary-500 animate-spin" />
          ) : (
            getStatusIcon()
          )}
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
            {getStatusMessage()}
          </span>
        </div>
        <button className="p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded transition-colors">
          {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {/* Progress Steps */}
      {isExpanded && (
        <div className="p-4 space-y-3">
          {/* Progress Bar */}
          <div className="h-1.5 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-primary-500 to-teal-500 rounded-full transition-all duration-500"
              style={{ 
                width: currentStatus === 'completed' ? '100%' : 
                       currentStatus === 'sending_email' ? '80%' :
                       currentStatus === 'creating_order' ? '60%' :
                       currentStatus === 'checking_safety' ? '40%' :
                       currentStatus === 'thinking' ? '20%' : '0%'
              }}
            />
          </div>

          {/* Step Items */}
          <div className="space-y-2">
            {steps.map((step, index) => (
              <div 
                key={step.id}
                className={`flex items-center gap-3 p-2 rounded-lg transition-colors ${
                  step.status === 'in_progress' ? 'bg-primary-50 dark:bg-primary-900/20' :
                  step.status === 'completed' ? 'bg-green-50 dark:bg-green-900/20' :
                  step.status === 'error' ? 'bg-red-50 dark:bg-red-900/20' :
                  'bg-slate-50 dark:bg-slate-700/30'
                }`}
              >
                {/* Step Icon */}
                <div className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                  step.status === 'completed' ? 'bg-green-500' :
                  step.status === 'in_progress' ? 'bg-primary-500' :
                  step.status === 'error' ? 'bg-red-500' :
                  'bg-slate-300 dark:bg-slate-600'
                }`}>
                  {step.status === 'completed' ? (
                    <CheckCircle size={14} className="text-white" />
                  ) : step.status === 'in_progress' ? (
                    <Loader2 size={12} className="text-white animate-spin" />
                  ) : step.status === 'error' ? (
                    <XCircle size={14} className="text-white" />
                  ) : (
                    <span className="text-xs text-white">{index + 1}</span>
                  )}
                </div>

                {/* Step Label */}
                <span className={`text-sm ${
                  step.status === 'in_progress' ? 'font-medium text-primary-700 dark:text-primary-300' :
                  step.status === 'completed' ? 'text-green-700 dark:text-green-300' :
                  step.status === 'error' ? 'text-red-700 dark:text-red-300' :
                  'text-slate-500 dark:text-slate-400'
                }`}>
                  {step.label}
                </span>

                {/* Step Details */}
                {step.details && step.status === 'in_progress' && (
                  <span className="text-xs text-slate-400 dark:text-slate-500 animate-pulse">
                    {step.details}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// Compact version for inline use
export function StatusBarCompact({ isVisible, currentStatus }: { isVisible: boolean; currentStatus: AgentStatus }) {
  if (!isVisible || currentStatus === 'idle') {
    return null;
  }

  const getStatusIcon = () => {
    switch (currentStatus) {
      case 'thinking':
        return <Brain size={14} className="text-blue-500" />;
      case 'checking_safety':
        return <ShieldCheck size={14} className="text-amber-500" />;
      case 'creating_order':
        return <ShoppingCart size={14} className="text-purple-500" />;
      case 'sending_email':
        return <Mail size={14} className="text-teal-500" />;
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (currentStatus) {
      case 'thinking':
        return 'AI is thinking...';
      case 'checking_safety':
        return 'Checking safety...';
      case 'creating_order':
        return 'Creating order...';
      case 'sending_email':
        return 'Sending email...';
      default:
        return '';
    }
  };

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 dark:bg-slate-800 rounded-full">
      <Loader2 size={12} className="text-primary-500 animate-spin" />
      {getStatusIcon()}
      <span className="text-xs text-slate-600 dark:text-slate-400">{getStatusText()}</span>
    </div>
  );
}
