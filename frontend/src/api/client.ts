import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL as string;

if (!BASE_URL) {
  console.warn('[api] VITE_API_URL is not set — falling back to http://localhost:8000');
}

export const apiClient = axios.create({
  baseURL: BASE_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
});

// Attach Bearer token on every request
apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Normalise 401 → redirect to login
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  },
);

/** Extract a human-readable message from an Axios error. */
export function extractErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as Record<string, unknown> | undefined;
    if (data) {
      if (typeof data.detail === 'string') return data.detail;
      if (typeof data.detail === 'object' && data.detail !== null) {
        const d = data.detail as Record<string, unknown>;
        if (typeof d.message === 'string') return d.message;
      }
      if (Array.isArray(data.detail)) {
        const first = data.detail[0] as Record<string, unknown>;
        if (typeof first?.msg === 'string') return first.msg;
      }
    }
    const status = error.response?.status ?? 0;
    if (status === 403) return 'You do not have permission to perform this action.';
    if (status === 404) return 'The requested resource was not found.';
    if (status === 409) return 'This action conflicts with the current state.';
    if (status === 422) return 'The request data is invalid. Please check your input.';
    if (status >= 500) return 'A server error occurred. Please try again later.';
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return 'An unexpected error occurred.';
}
