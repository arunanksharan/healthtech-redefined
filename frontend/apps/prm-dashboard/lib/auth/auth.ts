/**
 * Authentication utilities
 * Handles JWT token management, user session, and auth state
 */

import { jwtDecode } from 'jwt-decode';

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'provider' | 'staff' | 'patient';
  org_id: string;
  permissions: string[];
  department?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  expires_in: number;
}

export interface DecodedToken {
  sub: string;
  email: string;
  name: string;
  role: string;
  org_id: string;
  permissions: string[];
  exp: number;
  iat: number;
}

// Storage keys
const ACCESS_TOKEN_KEY = 'auth_access_token';
const REFRESH_TOKEN_KEY = 'auth_refresh_token';
const USER_KEY = 'auth_user';

/**
 * Store auth tokens securely
 */
export function storeTokens(tokens: AuthTokens): void {
  if (typeof window === 'undefined') return;

  localStorage.setItem(ACCESS_TOKEN_KEY, tokens.access_token);
  localStorage.setItem(REFRESH_TOKEN_KEY, tokens.refresh_token);

  // Decode and store user info
  try {
    const decoded = jwtDecode<DecodedToken>(tokens.access_token);
    const user: User = {
      id: decoded.sub,
      email: decoded.email,
      name: decoded.name,
      role: decoded.role as User['role'],
      org_id: decoded.org_id,
      permissions: decoded.permissions,
    };
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  } catch (error) {
    console.error('Failed to decode token:', error);
  }
}

/**
 * Get access token
 */
export function getAccessToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Get refresh token
 */
export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * Get current user
 */
export function getCurrentUser(): User | null {
  if (typeof window === 'undefined') return null;

  const userStr = localStorage.getItem(USER_KEY);
  if (!userStr) return null;

  try {
    return JSON.parse(userStr);
  } catch (error) {
    console.error('Failed to parse user:', error);
    return null;
  }
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  const token = getAccessToken();
  if (!token) return false;

  try {
    const decoded = jwtDecode<DecodedToken>(token);
    const now = Date.now() / 1000;
    return decoded.exp > now;
  } catch (error) {
    return false;
  }
}

/**
 * Check if token is expired
 */
export function isTokenExpired(token: string): boolean {
  try {
    const decoded = jwtDecode<DecodedToken>(token);
    const now = Date.now() / 1000;
    return decoded.exp <= now;
  } catch (error) {
    return true;
  }
}

/**
 * Check if token will expire soon (within 5 minutes)
 */
export function isTokenExpiringSoon(token: string): boolean {
  try {
    const decoded = jwtDecode<DecodedToken>(token);
    const now = Date.now() / 1000;
    const fiveMinutes = 5 * 60;
    return decoded.exp - now <= fiveMinutes;
  } catch (error) {
    return true;
  }
}

/**
 * Clear auth data (logout)
 */
export function clearAuth(): void {
  if (typeof window === 'undefined') return;

  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

/**
 * Check if user has permission
 */
export function hasPermission(permission: string): boolean {
  const user = getCurrentUser();
  if (!user) return false;

  // Admin has all permissions
  if (user.role === 'admin') return true;

  return user.permissions.includes(permission);
}

/**
 * Check if user has any of the permissions
 */
export function hasAnyPermission(permissions: string[]): boolean {
  return permissions.some((permission) => hasPermission(permission));
}

/**
 * Check if user has all permissions
 */
export function hasAllPermissions(permissions: string[]): boolean {
  return permissions.every((permission) => hasPermission(permission));
}

/**
 * Check if user has role
 */
export function hasRole(role: User['role'] | User['role'][]): boolean {
  const user = getCurrentUser();
  if (!user) return false;

  if (Array.isArray(role)) {
    return role.includes(user.role);
  }

  return user.role === role;
}

/**
 * Get time until token expires (in seconds)
 */
export function getTokenExpiryTime(token: string): number | null {
  try {
    const decoded = jwtDecode<DecodedToken>(token);
    const now = Date.now() / 1000;
    return Math.max(0, decoded.exp - now);
  } catch (error) {
    return null;
  }
}

/**
 * Validate token format
 */
export function isValidTokenFormat(token: string): boolean {
  // JWT format: header.payload.signature
  const parts = token.split('.');
  return parts.length === 3;
}
