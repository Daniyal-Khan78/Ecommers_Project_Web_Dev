// The base URL of our Django backend.
// All API calls will start with this URL.
// Change this when deploying to production.
export const API_BASE_URL = 'http://localhost:8000/api';

// Helper function to build a complete API URL from a path
// Example: buildUrl('/products/') → 'http://localhost:8000/api/products/'
export const buildUrl = (path) => `${API_BASE_URL}${path}`;

// Helper function that returns headers for authenticated requests.
// It reads the JWT access token from localStorage and attaches it.
// Django's DRF uses this token to identify who is making the request.
export const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};

// Helper for multipart form data (used when uploading images).
// Note: Do NOT set Content-Type here — the browser sets it automatically
// with the correct boundary for multipart/form-data.
export const getAuthHeadersMultipart = () => {
  const token = localStorage.getItem('access_token');
  return {
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
};
