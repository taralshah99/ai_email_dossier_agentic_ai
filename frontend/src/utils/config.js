// Configuration for API endpoints
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';

export const API_BASE_URL = BACKEND_URL;

// Helper function to build full API URLs
export const buildApiUrl = (endpoint) => {
  // Remove leading slash if present to avoid double slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  return `${API_BASE_URL}/${cleanEndpoint}`;
};

export default {
  API_BASE_URL,
  buildApiUrl
};
