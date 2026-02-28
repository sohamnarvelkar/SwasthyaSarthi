'use client';

import React, { ReactNode } from 'react';
import { useAuth } from '@/context/AuthContext';
import { LoginPage } from './LoginPage';
import { Loader2 } from 'lucide-react';

interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <div className="w-16 h-16 bg-gradient-to-br from-teal-400 to-blue-500 rounded-2xl flex items-center justify-center shadow-lg">
              <span className="text-3xl">🩺</span>
            </div>
            <div className="absolute inset-0 rounded-2xl border-2 border-teal-400/30 animate-ping" />
          </div>
          <Loader2 size={24} className="text-teal-400 animate-spin" />
          <p className="text-blue-200 text-sm">Loading SwasthyaSarthi...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  return <>{children}</>;
}
