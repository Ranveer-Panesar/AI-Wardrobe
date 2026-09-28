import React, { createContext, useState, useContext, useEffect } from 'react';

// 1. Create the Context
const AuthContext = createContext();

// 2. Custom hook so components can easily grab auth data
export const useAuth = () => useContext(AuthContext);

// 3. The Provider that will wrap the App
export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);

  // Check if a user was already logged in (persists after refresh)
  useEffect(() => {
    const storedUser = localStorage.getItem('ai_wardrobe_user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
  }, []);

  // Login function
  const login = (userData) => {
    // Generate a default profile picture if one isn't provided
    const avatar = userData.avatar || `https://api.dicebear.com/7.x/notionists/svg?seed=${userData.name || 'User'}`;
    
    const fullUser = {
      ...userData,
      avatar: avatar
    };

    setUser(fullUser);
    localStorage.setItem('ai_wardrobe_user', JSON.stringify(fullUser));
  };

  // Update profile picture function (for future settings page)
  const updateProfilePicture = (newAvatarUrl) => {
    if (!user) return;
    const updatedUser = { ...user, avatar: newAvatarUrl };
    setUser(updatedUser);
    localStorage.setItem('ai_wardrobe_user', JSON.stringify(updatedUser));
  };

  // Logout function
  const logout = () => {
    setUser(null);
    localStorage.removeItem('ai_wardrobe_user');
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, updateProfilePicture }}>
      {children}
    </AuthContext.Provider>
  );
};
