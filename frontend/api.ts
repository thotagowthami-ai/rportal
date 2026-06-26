import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Helper to ensure API_URL is defined at runtime
export function getApiUrl(): string {
  // If the configured URL is the Railway domain, use the Next.js rewrite proxy to bypass ISP DNS blocks
  if (API_URL && API_URL.includes('recruitcore-production.up.railway.app')) {
    return '/api/backend';
  }
  
  if (!API_URL) {
    throw new Error('NEXT_PUBLIC_API_URL is required');
  }
  return API_URL;
}

export const api = axios.create({
  baseURL: API_URL || undefined,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests and validate API URL at runtime
api.interceptors.request.use((config) => {
  try {
    config.baseURL = getApiUrl();
  } catch (error) {
    return Promise.reject(error);
  }

  const token =
    typeof window !== 'undefined' ? window.localStorage.getItem('access_token') : null;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle global 401 errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem('access_token');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
