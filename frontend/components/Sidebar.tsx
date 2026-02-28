'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { MessageSquare, Plus, Trash2, Mic, MicOff, Sun, Moon, LogOut, User, Pill, FileText, Clock, Search } from 'lucide-react';
import { ChatMessage } from '@/services/api';

interface SidebarProps {
  conversations: { id: string; title: string; messages: ChatMessage[] }[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
  isVoiceMode: boolean;
  onToggleVoiceMode: () => void;
  isDarkMode: boolean;
  onToggleDarkMode: () => void;
  userEmail?: string;
  onLogout?: () => void;
}

export function Sidebar({
  conversations,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  isVoiceMode,
  onToggleVoiceMode,
  isDarkMode,
  onToggleDarkMode,
  userEmail,
  onLogout,
}: SidebarProps) {
  const router = useRouter();

  const handleNavigateToMedicines = () => {
    router.push('/medicines');
  };

  return (
    <div className="w-64 h-full bg-slate-50 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-700 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-slate-200 dark:border-slate-700">
        <h1 className="text-xl font-bold text-healthcare flex items-center gap-2">
          <span className="text-2xl">🩺</span>
          SwasthyaSarthi
        </h1>
        <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
          AI Pharmacy Assistant
        </p>
      </div>

      {/* Quick Tools Grid */}
      <div className="p-3 border-b border-slate-200 dark:border-slate-700">
        <h3 className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase mb-2">
          Quick Tools
        </h3>
        <div className="grid grid-cols-2 gap-2">
          <button
            onClick={handleNavigateToMedicines}
            className="flex flex-col items-center gap-1 p-3 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-primary-50 dark:hover:bg-primary-900/30 transition-colors"
            title="Browse Medicines"
          >
            <Pill size={20} className="text-primary-500" />
            <span className="text-xs font-medium text-slate-600 dark:text-slate-300">Medicines</span>
          </button>
          
          <button
            onClick={onNewConversation}
            className="flex flex-col items-center gap-1 p-3 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-blue-50 dark:hover:bg-blue-900/30 transition-colors"
            title="Upload Prescription"
          >
            <FileText size={20} className="text-blue-500" />
            <span className="text-xs font-medium text-slate-600 dark:text-slate-300">Prescription</span>
          </button>
          
          <button
            onClick={onNewConversation}
            className="flex flex-col items-center gap-1 p-3 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-green-50 dark:hover:bg-green-900/30 transition-colors"
            title="Order History"
          >
            <Search size={20} className="text-green-500" />
            <span className="text-xs font-medium text-slate-600 dark:text-slate-300">Orders</span>
          </button>
          
          <button
            onClick={onNewConversation}
            className="flex flex-col items-center gap-1 p-3 rounded-lg bg-slate-100 dark:bg-slate-800 hover:bg-orange-50 dark:hover:bg-orange-900/30 transition-colors"
            title="Refill Reminders"
          >
            <Clock size={20} className="text-orange-500" />
            <span className="text-xs font-medium text-slate-600 dark:text-slate-300">Refills</span>
          </button>
        </div>
      </div>

      {/* New conversation button */}
      <div className="p-3">
        <button
          onClick={onNewConversation}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-primary-500 hover:bg-primary-600 text-white rounded-lg font-medium transition-colors"
        >
          <Plus size={18} />
          New Chat
        </button>
      </div>

      {/* Conversations list */}
      <div className="flex-1 overflow-y-auto p-2">
        {conversations.length === 0 ? (
          <p className="text-sm text-slate-500 dark:text-slate-400 text-center py-4">
            No conversations yet
          </p>
        ) : (
          <div className="space-y-1">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors ${
                  activeConversationId === conv.id
                    ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                    : 'hover:bg-slate-200 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
                }`}
                onClick={() => onSelectConversation(conv.id)}
              >
                <MessageSquare size={16} className="flex-shrink-0" />
                <span className="flex-1 truncate text-sm">{conv.title}</span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteConversation(conv.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-slate-300 dark:hover:bg-slate-700 rounded transition-opacity"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* User Profile Section */}
      {userEmail && (
        <div className="p-3 border-t border-slate-200 dark:border-slate-700">
          <div className="flex items-center gap-3 p-2 bg-slate-100 dark:bg-slate-800 rounded-lg">
            <div className="w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center">
              <User size={16} className="text-white" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300 truncate">
                {userEmail}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Bottom controls */}
      <div className="p-3 border-t border-slate-200 dark:border-slate-700 space-y-2">
        {/* Voice mode toggle */}
        <button
          onClick={onToggleVoiceMode}
          className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium transition-colors ${
            isVoiceMode
              ? 'bg-healthcare text-white'
              : 'bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-700'
          }`}
        >
          {isVoiceMode ? <Mic size={18} /> : <MicOff size={18} />}
          {isVoiceMode ? 'Voice Mode On' : 'Voice Mode'}
        </button>

        {/* Dark mode toggle */}
        <button
          onClick={onToggleDarkMode}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-300 dark:hover:bg-slate-700 transition-colors"
        >
          {isDarkMode ? <Sun size={18} /> : <Moon size={18} />}
          {isDarkMode ? 'Light Mode' : 'Dark Mode'}
        </button>

        {/* Logout button */}
        {onLogout && (
          <button
            onClick={onLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 hover:bg-red-100 dark:hover:bg-red-900/40 transition-colors"
          >
            <LogOut size={18} />
            Logout
          </button>
        )}
      </div>
    </div>
  );
}
