import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL;

// Helper to ensure API_URL is defined at runtime
export function getApiUrl(): string {
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

export default api;
