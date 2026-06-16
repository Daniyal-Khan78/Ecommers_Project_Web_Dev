import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

// createContext() creates a "global store" that any component can read from.
// We export AuthContext so components can subscribe to it.
const AuthContext = createContext(null);

// Custom hook — components call useAuth() instead of useContext(AuthContext)
// This gives a cleaner API and a helpful error if used outside the provider.
export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used inside an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  // user: the full user profile object (id, email, name, is_admin, etc.)
  // null means not logged in
  const [user, setUser]       = useState(null);
  const [loading, setLoading] = useState(true); // true while we check localStorage on mount

  // On first load, restore user session from localStorage.
  // This keeps the user logged in across page refreshes.
  useEffect(() => {
    const storedUser  = localStorage.getItem('user');
    const accessToken = localStorage.getItem('access_token');

    if (storedUser && accessToken) {
      try {
        setUser(JSON.parse(storedUser));
      } catch {
        // Corrupted data — clear it
        localStorage.removeItem('user');
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
      }
    }
    setLoading(false);
  }, []);

  // login: called after successful API login/register
  // Stores tokens and user in localStorage for persistence across refreshes
  const login = useCallback((userData, tokens) => {
    localStorage.setItem('access_token',  tokens.access);
    localStorage.setItem('refresh_token', tokens.refresh);
    localStorage.setItem('user',          JSON.stringify(userData));
    setUser(userData);
  }, []);

  // logout: clears all auth state
  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
  }, []);

  // updateUser: called after profile update to keep context in sync
  const updateUser = useCallback((updatedData) => {
    const updated = { ...user, ...updatedData };
    localStorage.setItem('user', JSON.stringify(updated));
    setUser(updated);
  }, [user]);

  // Computed values — derived from user state
  const isAuthenticated = !!user;
  const isAdmin         = user?.is_admin || user?.is_staff || false;

  const value = {
    user,
    isAuthenticated,
    isAdmin,
    loading,
    login,
    logout,
    updateUser,
  };

  // Don't render children until we've checked localStorage (avoids flash of unauthenticated UI)
  if (loading) return null;

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
