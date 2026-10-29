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

// Request interceptor: Inject JWT Bearer Token and X-Request-ID
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('shortdrama_auth_token');
    if (token && config.headers) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    // Generate UUID or timestamp-based request ID for tracing
    const reqId = typeof crypto !== 'undefined' && crypto.randomUUID 
      ? crypto.randomUUID() 
      : `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    if (config.headers) {
      config.headers['X-Request-ID'] = reqId;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for centralized error logging & 401 redirect
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const errorMsg = error.response?.data?.message || error.response?.data?.detail || error.message || 'Unknown network error';

    if (status === 401) {
      console.warn('[API Auth] 401 Unauthorized encountered, clearing session.');
      localStorage.removeItem('shortdrama_auth_token');
      localStorage.removeItem('shortdrama_user_info');
      if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
        window.location.href = `/login?redirect=${encodeURIComponent(window.location.pathname)}`;
      }
    }

    console.error(`[API Error] ${error.config?.method?.toUpperCase()} ${error.config?.url}:`, errorMsg);
    return Promise.reject(error);
  }
);

export function getMediaUrl(path: string): string {
  if (!path) return '';
  if (path.startsWith('http://') || path.startsWith('https://')) {
    return path;
  }
  const normalized = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalized}`;
}

export function getWsUrl(endpoint: string): string {
  if (import.meta.env.VITE_WS_URL) {
    return `${import.meta.env.VITE_WS_URL}${endpoint}`;
  }
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}${endpoint}`;
}

export default apiClient;
