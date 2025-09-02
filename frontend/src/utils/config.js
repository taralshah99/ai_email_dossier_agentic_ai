// Configuration for API endpoints
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export const API_BASE_URL = BACKEND_URL;

// Helper function to build full API URLs
export const buildApiUrl = (endpoint) => {
  // Remove leading slash if present to avoid double slashes
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint.slice(1) : endpoint;
  
  // Remove trailing slash from BACKEND_URL if present
  const cleanBackendUrl = BACKEND_URL.endsWith('/') ? BACKEND_URL.slice(0, -1) : BACKEND_URL;
  
  return `${cleanBackendUrl}/${cleanEndpoint}`;
};

export default {
  API_BASE_URL,
  buildApiUrl
};