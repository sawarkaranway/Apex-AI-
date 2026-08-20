import React, { createContext, useContext, useState, useEffect } from 'react';
import api from '../lib/api';

interface User {
  pk: number;
  email: string;
  first_name?: string;
  last_name?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const getInitialToken = () => {
    try {
      const hash = window.location.hash || '';
      const search = window.location.search || '';
      const queryString = search ? search.substring(1) : (hash.includes('?') ? hash.split('?')[1] : '');
      if (queryString) {
        const urlParams = new URLSearchParams(queryString);
        const urlToken = urlParams.get('token') || urlParams.get('access_token');
        if (urlToken) {
          localStorage.setItem('auth_token', urlToken);
          if (window.history.replaceState) {
            window.history.replaceState({}, document.title, window.location.pathname + '#/');
          }
          return urlToken;
        }
      }
    } catch (e) {
      console.warn('Failed to parse URL token:', e);
    }
    return localStorage.getItem('auth_token');
  };

  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(getInitialToken);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (token) {
      api.setToken(token);
      api.get<User>('/auth/user/')
        .then((userData) => {
          setUser(userData);
          setIsLoading(false);
        })
        .catch(() => {
          logout();
          setIsLoading(false);
        });
    } else {
      setIsLoading(false);
    }
  }, [token]);

  const login = (newToken: string, userData: User) => {
    localStorage.setItem('auth_token', newToken);
    setToken(newToken);
    setUser(userData);
    api.setToken(newToken);
  };

  const logout = async () => {
    try {
      if (token) {
        await api.post('/auth/logout/');
      }
    } catch (e) {
      console.warn('Logout failed on backend');
    }
    localStorage.removeItem('auth_token');
    setToken(null);
    setUser(null);
    api.setToken(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
