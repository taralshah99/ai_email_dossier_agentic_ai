import axios from 'axios';

// Configure axios defaults for authentication
export const setupAxiosDefaults = () => {
  // Always send cookies with requests
  axios.defaults.withCredentials = true;
  
  // Add request interceptor to handle authentication
  axios.interceptors.request.use(
    (config) => {
      // Add any additional headers if needed
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Add response interceptor to handle authentication errors
  axios.interceptors.response.use(
    (response) => {
      return response;
    },
    (error) => {
      if (error.response?.status === 401) {
        // Handle unauthorized access
        console.warn('Authentication required - redirecting to login');
        
        // You could dispatch a logout action here if using Redux
        // or trigger a re-authentication flow
        
        // For now, we'll let the component handle it
      }
      
      return Promise.reject(error);
    }
  );
};

// Helper function to check if error is authentication-related
export const isAuthError = (error) => {
  return error.response?.status === 401 || 
         error.response?.data?.error === 'Authentication required';
};

// Helper function to handle API errors with user-friendly messages
export const getErrorMessage = (error) => {
  if (isAuthError(error)) {
    return 'Please log in to continue.';
  }
  
  if (error.response?.data?.error) {
    return error.response.data.error;
  }
  
  if (error.message) {
    return error.message;
  }
  
  return 'An unexpected error occurred. Please try again.';
};

// Helper function to make authenticated API calls
export const authenticatedRequest = async (requestFn) => {
  try {
    return await requestFn();
  } catch (error) {
    if (isAuthError(error)) {
      // Could trigger a re-authentication flow here
      throw new Error('Authentication required');
    }
    throw error;
  }
};

// Helper to format user display name
export const formatUserDisplayName = (user) => {
  if (!user?.email) return 'Unknown User';
  
  const localPart = user.email.split('@')[0];
  
  // Handle common email formats
  if (localPart.includes('.')) {
    return localPart
      .split('.')
      .map(part => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  }
  
  if (localPart.includes('_')) {
    return localPart
      .split('_')
      .map(part => part.charAt(0).toUpperCase() + part.slice(1))
      .join(' ');
  }
  
  return localPart.charAt(0).toUpperCase() + localPart.slice(1);
};

// Helper to get user initials for avatar
export const getUserInitials = (user) => {
  if (!user?.email) return 'U';
  
  const email = user.email.toLowerCase();
  const localPart = email.split('@')[0];
  
  if (localPart.includes('.')) {
    const parts = localPart.split('.');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
  }
  
  if (localPart.includes('_')) {
    const parts = localPart.split('_');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
  }
  
  return localPart[0].toUpperCase();
};

// Helper to validate session on app startup
export const validateSession = async () => {
  try {
    const response = await axios.get('/api/auth/status');
    return response.data.authenticated === true;
  } catch (error) {
    console.error('Session validation failed:', error);
    return false;
  }
};

export default {
  setupAxiosDefaults,
  isAuthError,
  getErrorMessage,
  authenticatedRequest,
  formatUserDisplayName,
  getUserInitials,
  validateSession
};