import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

const TOKEN_KEY = 'ai_wardrobe_token';
const USER_KEY  = 'ai_wardrobe_user';

export const AuthProvider = ({ children }) => {
  const [user, setUser]   = useState(null);
  const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));

  // Rehydrate user from storage on mount
  useEffect(() => {
    const storedUser  = localStorage.getItem(USER_KEY);
    const storedToken = localStorage.getItem(TOKEN_KEY);
    if (storedUser && storedToken) {
      try {
        setUser(JSON.parse(storedUser));
        setToken(storedToken);
      } catch {
        localStorage.removeItem(USER_KEY);
        localStorage.removeItem(TOKEN_KEY);
      }
    }
  }, []);

  /**
   * Call after a successful /auth/login or /auth/signup.
   * @param {object} userData  - { email, name?, avatar? }
   * @param {string} accessToken - JWT access_token from the backend
   */
  const login = useCallback((userData, accessToken) => {
    const avatar = userData.avatar ||
      `https://api.dicebear.com/7.x/notionists/svg?seed=${userData.name || userData.email || 'User'}`;

    const fullUser = { ...userData, avatar };

    setUser(fullUser);
    setToken(accessToken);
    localStorage.setItem(USER_KEY, JSON.stringify(fullUser));

    // This is what apiFetch reads for Authorization: Bearer <token>
    if (accessToken) {
      localStorage.setItem(TOKEN_KEY, accessToken);
    }
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(TOKEN_KEY);
  }, []);

  // Listen to 401 unauth logout events dispatched by client.js
  useEffect(() => {
    const handleAuthLogout = () => logout();
    window.addEventListener('auth:logout', handleAuthLogout);
    return () => window.removeEventListener('auth:logout', handleAuthLogout);
  }, [logout]);

  const updateProfilePicture = useCallback((newAvatarUrl) => {
    setUser(prev => {
      if (!prev) return null;
      const updatedUser = { ...prev, avatar: newAvatarUrl };
      localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
      return updatedUser;
    });
  }, []);

  const isLoggedIn = Boolean(user && token);

  return (
    <AuthContext.Provider value={{ user, token, isLoggedIn, login, logout, updateProfilePicture }}>
      {children}
    </AuthContext.Provider>
  );
};

