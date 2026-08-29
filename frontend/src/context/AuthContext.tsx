import React, { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { login as apiLogin, getCurrentUser } from '../api/auth';
import type { User, LoginCredentials } from '../types';

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextValue extends AuthState {
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<AuthState>({
    user: null,
    isAuthenticated: false,
    isLoading: true,
  });

  const refreshUser = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setState({ user: null, isAuthenticated: false, isLoading: false });
      return;
    }
    try {
      const user = await getCurrentUser();
      setState({ user, isAuthenticated: true, isLoading: false });
    } catch {
      localStorage.removeItem('access_token');
      setState({ user: null, isAuthenticated: false, isLoading: false });
    }
  }, []);

  // Rehydrate auth state on mount (survives page refresh)
  useEffect(() => {
    void refreshUser();
  }, [refreshUser]);

  const login = useCallback(async (credentials: LoginCredentials) => {
    const { access_token } = await apiLogin(credentials);
    localStorage.setItem('access_token', access_token);
    const user = await getCurrentUser();
    setState({ user, isAuthenticated: true, isLoading: false });
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    setState({ user: null, isAuthenticated: false, isLoading: false });
  }, []);

  return (
    <AuthContext.Provider value={{ ...state, login, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
