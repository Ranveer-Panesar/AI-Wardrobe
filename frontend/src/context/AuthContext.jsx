import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { login as apiLogin, signup as apiSignup } from '../api/auth';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('ai_wardrobe_token'));

  // Listen for 401 events fired by the API client
  useEffect(() => {
    const handleLogout = () => {
      setToken(null);
      localStorage.removeItem('ai_wardrobe_token');
    };
    window.addEventListener('auth:logout', handleLogout);
    return () => window.removeEventListener('auth:logout', handleLogout);
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await apiLogin(email, password);
    localStorage.setItem('ai_wardrobe_token', data.access_token);
    setToken(data.access_token);
  }, []);

  const signup = useCallback(async (email, phone, password) => {
    await apiSignup(email, phone, password);
    // Auto-login after sign up
    await login(email, password);
  }, [login]);

  const logout = useCallback(() => {
    localStorage.removeItem('ai_wardrobe_token');
    setToken(null);
  }, []);

  return (
    <AuthContext.Provider value={{ token, isLoggedIn: !!token, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
