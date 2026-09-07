import axios from 'axios';

// Resolve base URL: In dev Vite proxies /api, in prod it can use custom VITE_API_BASE_URL or relative
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// Create unified axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for centralized error logging
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const errorMsg = error.response?.data?.detail || error.message || 'Unknown network error';
    console.error(`[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}:`, errorMsg);
    return Promise.reject(error);
  }
);

export function getMediaUrl(path: string): string {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  // Ensure starts with '/'
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalized}`;
}

export function getWsUrl(endpoint: string): string {
  if (import.meta.env.VITE_WS_URL) {
    return `${import.meta.env.VITE_WS_URL}${endpoint}`;
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  // If in dev and proxied, or same host
  return `${protocol}//${window.location.host}${endpoint}`;
}

export default apiClient;
