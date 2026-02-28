'use client';

import React, { useState, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import { Loader2, Mail, Lock, AlertCircle, Heart, User, CheckCircle } from 'lucide-react';

export function LoginPage() {
  const { login, register, isLoading, error } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoginMode, setIsLoginMode] = useState(true);
  const [localError, setLocalError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [fullName, setFullName] = useState('');

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalError(null);
    setSuccessMessage(null);

    if (!email.trim() || !password.trim()) {
      setLocalError('Please fill in all fields');
      return;
    }

    if (!email.includes('@')) {
      setLocalError('Please enter a valid email address');
      return;
    }

    if (password.length < 6) {
      setLocalError('Password must be at least 6 characters');
      return;
    }

    if (!isLoginMode) {
      // Sign up mode
      if (password !== confirmPassword) {
        setLocalError('Passwords do not match');
        return;
      }
      
      try {
        setLocalError(null);
        // The register function will auto-login after registration
        await register(email, password, fullName || undefined);
        setSuccessMessage('Account created! Sending login notification...');
      } catch (err) {
        // Error is handled by AuthContext
      }
    } else {
      // Login mode
      try {
        await login(email, password);
      } catch (err) {
        // Error is handled by AuthContext
      }
    }
  }, [email, password, confirmPassword, fullName, isLoginMode, login, register]);

  const switchMode = useCallback(() => {
    setIsLoginMode(!isLoginMode);
    setLocalError(null);
    setSuccessMessage(null);
  }, [isLoginMode]);

  const displayError = localError || error;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 relative overflow-hidden">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/20 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-teal-500/20 rounded-full blur-3xl animate-pulse-slow" style={{ animationDelay: '1s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl" />
      </div>

      {/* Floating medical icons */}
      <div className="absolute inset-0 pointer-events-none">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className="absolute text-white/10 animate-float"
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${i * 0.5}s`,
              animationDuration: `${3 + Math.random() * 2}s`,
            }}
          >
            {i % 3 === 0 ? '💊' : i % 3 === 1 ? '🩺' : '❤️'}
          </div>
        ))}
      </div>

      {/* Login/Signup Card */}
      <div className="relative z-10 w-full max-w-md px-4">
        <div className="bg-white/10 backdrop-blur-xl border border-white/20 rounded-3xl p-8 shadow-2xl">
          {/* Logo and Title */}
          <div className="text-center mb-6">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-teal-400 to-blue-500 rounded-2xl mb-4 shadow-lg">
              <span className="text-3xl">🩺</span>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">
              SwasthyaSarthi
            </h1>
            <p className="text-blue-200 text-sm">
              {isLoginMode ? 'Welcome back!' : 'Create your account'}
            </p>
          </div>

          {/* Success Message */}
          {successMessage && (
            <div className="flex items-center gap-2 p-3 mb-4 bg-green-500/20 border border-green-500/30 rounded-xl text-green-200 text-sm">
              <CheckCircle size={16} />
              <span>{successMessage}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full Name (Sign up only) */}
            {!isLoginMode && (
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 text-blue-300" size={20} />
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Full Name (optional)"
                  className="w-full pl-12 pr-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-blue-200/60 focus:outline-none focus:ring-2 focus:ring-teal-400 focus:border-transparent transition-all"
                  disabled={isLoading}
                />
              </div>
            )}

            {/* Email Input */}
            <div className="relative">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 text-blue-300" size={20} />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email address"
                className="w-full pl-12 pr-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-blue-200/60 focus:outline-none focus:ring-2 focus:ring-teal-400 focus:border-transparent transition-all"
                disabled={isLoading}
              />
            </div>

            {/* Password Input */}
            <div className="relative">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-blue-300" size={20} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                className="w-full pl-12 pr-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-blue-200/60 focus:outline-none focus:ring-2 focus:ring-teal-400 focus:border-transparent transition-all"
                disabled={isLoading}
              />
            </div>

            {/* Confirm Password (Sign up only) */}
            {!isLoginMode && (
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 text-blue-300" size={20} />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Confirm password"
                  className="w-full pl-12 pr-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-blue-200/60 focus:outline-none focus:ring-2 focus:ring-teal-400 focus:border-transparent transition-all"
                  disabled={isLoading}
                />
              </div>
            )}

            {/* Error Message */}
            {displayError && (
              <div className="flex items-center gap-2 p-3 bg-red-500/20 border border-red-500/30 rounded-xl text-red-200 text-sm">
                <AlertCircle size={16} />
                <span>{displayError}</span>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-3.5 bg-gradient-to-r from-teal-500 to-blue-500 hover:from-teal-400 hover:to-blue-400 text-white font-semibold rounded-xl transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader2 size={20} className="animate-spin" />
                  <span>Please wait...</span>
                </>
              ) : (
                <>
                  <Heart size={20} className="text-white/80" />
                  <span>{isLoginMode ? 'Sign In' : 'Create Account'}</span>
                </>
              )}
            </button>
          </form>

          {/* Switch Mode */}
          <div className="mt-6 text-center">
            <p className="text-blue-200 text-sm">
              {isLoginMode ? "Don't have an account?" : 'Already have an account?'}
              <button
                type="button"
                onClick={switchMode}
                className="ml-2 text-teal-300 hover:text-teal-200 font-medium underline underline-offset-2"
              >
                {isLoginMode ? 'Sign Up' : 'Sign In'}
              </button>
            </p>
          </div>

          {/* Info for Sign up */}
          {!isLoginMode && (
            <div className="mt-4 p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl">
              <p className="text-blue-200 text-xs text-center">
                📧 We'll send a login notification to your email
              </p>
              <p className="text-blue-200 text-xs text-center mt-1">
                📦 Order confirmations will be sent to {email || 'your email'}
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-6 text-center">
          <p className="text-blue-200/60 text-xs">
            By continuing, you agree to our Terms of Service and Privacy Policy
          </p>
        </div>

        {/* Language selector */}
        <div className="mt-4 flex justify-center gap-2">
          {['English', 'हिंदी', 'मराठी'].map((lang) => (
            <button
              key={lang}
              className="px-3 py-1.5 text-sm text-blue-200 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            >
              {lang}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
