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
      console.log('Checking auth status...');
      const response = await axios.get('/api/auth/status');
      console.log('Auth status response:', response.data);
      
      if (response.data.authenticated) {
        console.log('User is authenticated:', response.data.user);
        setIsAuthenticated(true);
        setUser(response.data.user);
      } else {
        console.log('User is not authenticated');
        setIsAuthenticated(false);
        setUser(null);
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
      console.error('Auth status error details:', error.response);
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
    
    console.log('Checking OAuth callback, URL params:', window.location.search);
    console.log('Auth status from URL:', authStatus);
    
    if (authStatus === 'success') {
      console.log('OAuth success detected, clearing URL and checking auth...');
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
    } else if (authStatus) {
      console.log('Unknown auth status:', authStatus);
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
