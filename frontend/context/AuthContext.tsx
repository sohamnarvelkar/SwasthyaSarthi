'use client';

import React, { createContext, useContext, useState, useCallback, useEffect, ReactNode } from 'react';
import { loginUser, registerUser, getCurrentUser, ChatMessage } from '@/services/api';

interface User {
  id: number;
  email: string;
  full_name: string;
  is_admin: boolean;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string) => Promise<void>;
  logout: () => void;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'swasthya_sarthi_token';
const USER_KEY = 'swasthya_sarthi_user';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Check for existing session on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem(TOKEN_KEY);
      const savedUser = localStorage.getItem(USER_KEY);
      
      if (token && savedUser) {
        try {
          const userData = JSON.parse(savedUser);
          setUser(userData);
          
          // Verify token is still valid
          try {
            const currentUser = await getCurrentUser(token);
            setUser(currentUser);
            localStorage.setItem(USER_KEY, JSON.stringify(currentUser));
          } catch {
            // Token invalid, clear session
            localStorage.removeItem(TOKEN_KEY);
            localStorage.removeItem(USER_KEY);
            setUser(null);
          }
        } catch {
          setUser(null);
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await loginUser(email, password);
      localStorage.setItem(TOKEN_KEY, response.access_token);
      
      const userData = await getCurrentUser(response.access_token);
      setUser(userData);
      localStorage.setItem(USER_KEY, JSON.stringify(userData));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (email: string, password: string, fullName?: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      await registerUser(email, password, fullName);
      // Auto-login after registration
      await login(email, password);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Registration failed';
      setError(message);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [login]);

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    setUser(null);
    setError(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
