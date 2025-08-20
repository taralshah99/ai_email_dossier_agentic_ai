import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  // Configure axios to include credentials in all requests
  axios.defaults.withCredentials = true;

  // Check authentication status on mount and handle OAuth callback
  useEffect(() => {
    checkAuthStatus();
    handleOAuthCallback();
  }, []);

  const checkAuthStatus = async () => {
    try {
      const response = await axios.get('/api/auth/status');
      if (response.data.authenticated) {
        setIsAuthenticated(true);
        setUser(response.data.user);
      } else {
        setIsAuthenticated(false);
        setUser(null);
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOAuthCallback = () => {
    // Check if we're returning from OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    const authStatus = urlParams.get('auth');
    
    if (authStatus === 'success') {
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);
      // Refresh auth status
      setTimeout(checkAuthStatus, 500);
    } else if (authStatus === 'error') {
      const errorMessage = urlParams.get('message');
      console.error('OAuth error:', errorMessage);
      // Clear URL parameters
      window.history.replaceState({}, document.title, window.location.pathname);
      setIsLoading(false);
    }
  };

  const login = async () => {
    try {
      const response = await axios.post('/api/auth/login');
      const { auth_url } = response.data;
      
      // Redirect to Google OAuth
      window.location.href = auth_url;
    } catch (error) {
      console.error('Login error:', error);
      throw new Error(
        error.response?.data?.error || 
        'Failed to initiate login. Please try again.'
      );
    }
  };

  const logout = async () => {
    setIsLoggingOut(true);
    try {
      await axios.post('/api/auth/logout');
      setIsAuthenticated(false);
      setUser(null);
    } catch (error) {
      console.error('Logout error:', error);
      // Still clear local state even if server logout fails
      setIsAuthenticated(false);
      setUser(null);
    } finally {
      setIsLoggingOut(false);
    }
  };

  const value = {
    isAuthenticated,
    user,
    isLoading,
    isLoggingOut,
    login,
    logout,
    checkAuthStatus
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
