import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import toast from 'react-hot-toast';

/**
 * API Client using latest Axios patterns
 * Configured for Next.js 15 with React 19
 */

// Create axios instance with default configuration
export const apiClient: AxiosInstance = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request Interceptor
 * Add authentication token and org context to all requests
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add auth token from localStorage (or your auth solution)
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('auth_token');
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      // Add organization ID to all requests only if it has a valid value
      const orgId = localStorage.getItem('org_id');
      if (orgId && orgId.trim() !== '') {
        if (config.params) {
          config.params.org_id = orgId;
        } else {
          config.params = { org_id: orgId };
        }
      }
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response Interceptor
 * Handle common errors and show toast notifications
 */
apiClient.interceptors.response.use(
  (response) => {
    // Success - return data directly
    return response;
  },
  (error: AxiosError<{ detail?: string | any[]; message?: string }>) => {
    // Handle different error status codes
    if (error.response) {
      const status = error.response.status;

      // Extract error message, handling FastAPI validation error format
      let message = 'An error occurred';
      const detail = error.response.data?.detail;

      if (typeof detail === 'string') {
        message = detail;
      } else if (Array.isArray(detail) && detail.length > 0) {
        // FastAPI validation errors are arrays of {loc, msg, type}
        message = detail.map(err => err.msg || JSON.stringify(err)).join(', ');
      } else if (error.response.data?.message) {
        message = error.response.data.message;
      }

      switch (status) {
        case 401:
          // Unauthorized - redirect to login
          toast.error('Session expired. Please login again.');
          if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
            window.location.href = '/login';
          }
          break;

        case 403:
          // Forbidden
          toast.error('You do not have permission to perform this action.');
          break;

        case 404:
          // Not found
          toast.error(message || 'Resource not found.');
          break;

        case 422:
          // Validation error
          toast.error(message || 'Validation error. Please check your input.');
          break;

        case 500:
          // Server error
          toast.error('Server error. Please try again later.');
          break;

        default:
          toast.error(message);
      }
    } else if (error.request) {
      // Request made but no response
      toast.error('Network error. Please check your connection.');
    } else {
      // Something else happened
      toast.error('An unexpected error occurred.');
    }

    return Promise.reject(error);
  }
);



/**
 * API Response Types
 */
export interface APIResponse<T> {
  data: T;
  message?: string;
  success: boolean;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface APIError {
  code: string;
  message: string;
  details?: any;
}

/**
 * Helper function for handling API calls with proper typing
 */
export async function apiCall<T>(
  promise: Promise<any>
): Promise<[T | null, APIError | null]> {
  try {
    const response = await promise;
    return [response.data, null];
  } catch (error: any) {
    // Extract error message, handling FastAPI validation error format
    let message = 'An error occurred';
    const detail = error.response?.data?.detail;

    if (typeof detail === 'string') {
      message = detail;
    } else if (Array.isArray(detail) && detail.length > 0) {
      // FastAPI validation errors are arrays of {loc, msg, type}
      message = detail.map((err: any) => err.msg || JSON.stringify(err)).join(', ');
    } else if (error.response?.data?.message) {
      message = error.response.data.message;
    } else if (error.message) {
      message = error.message;
    }

    const apiError: APIError = {
      code: error.response?.data?.code || 'UNKNOWN_ERROR',
      message,
      details: error.response?.data?.details || detail,
    };
    return [null, apiError];
  }
}
