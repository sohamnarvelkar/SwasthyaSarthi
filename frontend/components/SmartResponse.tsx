'use client';

import React from 'react';
import { Stethoscope, Pill, AlertTriangle, Info, CheckCircle, Clock, ArrowRight } from 'lucide-react';
import { Medicine, MedicineCard } from './MedicineCard';

export interface Condition {
  name: string;
  confidence: number;
  description: string;
}

export interface SafetyWarning {
  type: 'danger' | 'warning' | 'info';
  message: string;
}

export interface SmartResponseData {
  conditions?: Condition[];
  medicines?: Medicine[];
  advice?: string[];
  warnings?: SafetyWarning[];
  follow_up_questions?: string[];
}

interface SmartResponseProps {
  data: SmartResponseData;
  onOrderMedicine?: (medicine: Medicine, quantity: number) => void;
  onAskQuestion?: (question: string) => void;
}

export function SmartResponse({ data, onOrderMedicine, onAskQuestion }: SmartResponseProps) {
  return (
    <div className="space-y-4 my-4">
      {/* Possible Conditions */}
      {data.conditions && data.conditions.length > 0 && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-2xl p-4 border border-blue-100 dark:border-blue-800">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center">
              <Stethoscope size={16} className="text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="font-semibold text-blue-800 dark:text-blue-300">Possible Condition</h3>
          </div>
          <div className="space-y-2">
            {data.conditions.map((condition, index) => (
              <div key={index} className="flex items-start gap-3 p-3 bg-white dark:bg-slate-800 rounded-xl">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-slate-900 dark:text-white">{condition.name}</p>
                    <span className="text-xs px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-full">
                      {condition.confidence}% match
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">{condition.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Medicines */}
      {data.medicines && data.medicines.length > 0 && (
        <div className="bg-gradient-to-r from-teal-50 to-green-50 dark:from-teal-900/20 dark:to-green-900/20 rounded-2xl p-4 border border-teal-100 dark:border-teal-800">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 bg-teal-100 dark:bg-teal-900/30 rounded-lg flex items-center justify-center">
              <Pill size={16} className="text-teal-600 dark:text-teal-400" />
            </div>
            <h3 className="font-semibold text-teal-800 dark:text-teal-300">Recommended Medicines</h3>
          </div>
          <div className="space-y-3">
            {data.medicines.map((medicine) => (
              <MedicineCard
                key={medicine.id}
                medicine={medicine}
                onOrder={onOrderMedicine}
                compact
              />
            ))}
          </div>
        </div>
      )}

      {/* Safety Warnings */}
      {data.warnings && data.warnings.length > 0 && (
        <div className="bg-gradient-to-r from-amber-50 to-orange-50 dark:from-amber-900/20 dark:to-orange-900/20 rounded-2xl p-4 border border-amber-100 dark:border-amber-800">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 bg-amber-100 dark:bg-amber-900/30 rounded-lg flex items-center justify-center">
              <AlertTriangle size={16} className="text-amber-600 dark:text-amber-400" />
            </div>
            <h3 className="font-semibold text-amber-800 dark:text-amber-300">Safety Advice</h3>
          </div>
          <div className="space-y-2">
            {data.warnings.map((warning, index) => (
              <div
                key={index}
                className={`flex items-start gap-3 p-3 rounded-xl ${
                  warning.type === 'danger'
                    ? 'bg-red-50 dark:bg-red-900/20'
                    : warning.type === 'warning'
                    ? 'bg-amber-50 dark:bg-amber-900/20'
                    : 'bg-blue-50 dark:bg-blue-900/20'
                }`}
              >
                <AlertTriangle
                  size={16}
                  className={`mt-0.5 flex-shrink-0 ${
                    warning.type === 'danger'
                      ? 'text-red-500'
                      : warning.type === 'warning'
                      ? 'text-amber-500'
                      : 'text-blue-500'
                  }`}
                />
                <p className={`text-sm ${
                  warning.type === 'danger'
                    ? 'text-red-700 dark:text-red-300'
                    : warning.type === 'warning'
                    ? 'text-amber-700 dark:text-amber-300'
                    : 'text-blue-700 dark:text-blue-300'
                }`}>
                  {warning.message}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* General Advice */}
      {data.advice && data.advice.length > 0 && (
        <div className="bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-800/50 dark:to-slate-700/50 rounded-2xl p-4 border border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-8 h-8 bg-slate-200 dark:bg-slate-700 rounded-lg flex items-center justify-center">
              <Info size={16} className="text-slate-600 dark:text-slate-400" />
            </div>
            <h3 className="font-semibold text-slate-700 dark:text-slate-300">Health Tips</h3>
          </div>
          <ul className="space-y-2">
            {data.advice.map((tip, index) => (
              <li key={index} className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-400">
                <CheckCircle size={14} className="mt-0.5 text-green-500 flex-shrink-0" />
                <span>{tip}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Follow-up Questions */}
      {data.follow_up_questions && data.follow_up_questions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {data.follow_up_questions.map((question, index) => (
            <button
              key={index}
              onClick={() => onAskQuestion?.(question)}
              className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-full text-sm text-slate-600 dark:text-slate-400 hover:bg-primary-50 dark:hover:bg-primary-900/20 hover:border-primary-300 dark:hover:border-primary-700 transition-colors"
            >
              <Clock size={14} className="text-primary-500" />
              <span>{question}</span>
              <ArrowRight size={14} className="text-slate-400" />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// Helper function to parse AI response into structured data
export function parseSmartResponse(content: string): SmartResponseData | null {
  // Check if response contains structured markers
  const hasConditions = content.includes('🩺') || content.includes('Possible Condition');
  const hasMedicines = content.includes('💊') || content.includes('Medicine');
  const hasWarnings = content.includes('⚠️') || content.includes('Warning');

  if (!hasConditions && !hasMedicines && !hasWarnings) {
    return null;
  }

  // Simple parsing - in production this would be more sophisticated
  const data: SmartResponseData = {
    conditions: [],
    medicines: [],
    advice: [],
    warnings: [],
    follow_up_questions: [],
  };

  return data;
}
