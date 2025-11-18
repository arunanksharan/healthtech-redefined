/**
 * Session Management
 * Handles session lifecycle, timeout, and security
 */

import { clearAuth, isAuthenticated } from '../auth/auth';

const SESSION_TIMEOUT = 30 * 60 * 1000; // 30 minutes
const WARNING_BEFORE_TIMEOUT = 5 * 60 * 1000; // 5 minutes before timeout
const ACTIVITY_CHECK_INTERVAL = 60 * 1000; // Check every minute

let sessionTimer: NodeJS.Timeout | null = null;
let warningTimer: NodeJS.Timeout | null = null;
let activityCheckTimer: NodeJS.Timeout | null = null;
let lastActivityTime: number = Date.now();

export interface SessionConfig {
  timeout?: number;
  warningBefore?: number;
  onWarning?: () => void;
  onTimeout?: () => void;
}

/**
 * Initialize session management
 */
export function initSession(config: SessionConfig = {}): void {
  if (typeof window === 'undefined') return;

  const timeout = config.timeout || SESSION_TIMEOUT;
  const warningBefore = config.warningBefore || WARNING_BEFORE_TIMEOUT;

  // Clear existing timers
  clearSessionTimers();

  // Reset last activity
  lastActivityTime = Date.now();

  // Set up activity listeners
  setupActivityListeners();

  // Set up session timeout
  resetSessionTimeout(timeout, warningBefore, config);

  // Set up periodic activity check
  activityCheckTimer = setInterval(() => {
    checkSessionActivity(timeout, warningBefore, config);
  }, ACTIVITY_CHECK_INTERVAL);
}

/**
 * Reset session timeout
 */
export function resetSessionTimeout(
  timeout: number = SESSION_TIMEOUT,
  warningBefore: number = WARNING_BEFORE_TIMEOUT,
  config: SessionConfig = {}
): void {
  if (typeof window === 'undefined') return;

  // Clear existing timers
  if (sessionTimer) clearTimeout(sessionTimer);
  if (warningTimer) clearTimeout(warningTimer);

  // Set warning timer
  const warningTime = timeout - warningBefore;
  warningTimer = setTimeout(() => {
    if (config.onWarning) {
      config.onWarning();
    } else {
      showSessionWarning(Math.floor(warningBefore / 1000));
    }
  }, warningTime);

  // Set session timeout
  sessionTimer = setTimeout(() => {
    handleSessionTimeout(config);
  }, timeout);
}

/**
 * Update last activity time
 */
export function updateActivity(): void {
  lastActivityTime = Date.now();
}

/**
 * Check session activity
 */
function checkSessionActivity(
  timeout: number,
  warningBefore: number,
  config: SessionConfig
): void {
  const now = Date.now();
  const timeSinceActivity = now - lastActivityTime;

  // If activity detected, reset timeout
  if (timeSinceActivity < ACTIVITY_CHECK_INTERVAL * 2) {
    resetSessionTimeout(timeout, warningBefore, config);
  }
}

/**
 * Set up activity listeners
 */
function setupActivityListeners(): void {
  if (typeof window === 'undefined') return;

  const events = ['mousedown', 'keydown', 'scroll', 'touchstart', 'click'];

  const activityHandler = () => {
    updateActivity();
  };

  events.forEach((event) => {
    window.addEventListener(event, activityHandler, { passive: true });
  });
}

/**
 * Handle session timeout
 */
function handleSessionTimeout(config: SessionConfig): void {
  // Clear auth
  clearAuth();

  // Call custom handler or default
  if (config.onTimeout) {
    config.onTimeout();
  } else {
    // Redirect to login with timeout message
    window.location.href = '/login?reason=timeout';
  }
}

/**
 * Show session warning
 */
function showSessionWarning(secondsRemaining: number): void {
  const message = `Your session will expire in ${Math.floor(secondsRemaining / 60)} minutes due to inactivity. Click to continue.`;

  // Use browser notification if permitted
  if ('Notification' in window && Notification.permission === 'granted') {
    const notification = new Notification('Session Expiring', {
      body: message,
      icon: '/icon.png',
      requireInteraction: true,
    });

    notification.onclick = () => {
      updateActivity();
      notification.close();
    };
  } else {
    // Fallback to alert (in production, use a modal)
    const confirmed = confirm(message);
    if (confirmed) {
      updateActivity();
    }
  }
}

/**
 * Clear session timers
 */
export function clearSessionTimers(): void {
  if (sessionTimer) clearTimeout(sessionTimer);
  if (warningTimer) clearTimeout(warningTimer);
  if (activityCheckTimer) clearInterval(activityCheckTimer);

  sessionTimer = null;
  warningTimer = null;
  activityCheckTimer = null;
}

/**
 * Get session info
 */
export function getSessionInfo(): {
  isActive: boolean;
  lastActivity: number;
  timeSinceActivity: number;
} {
  return {
    isActive: isAuthenticated(),
    lastActivity: lastActivityTime,
    timeSinceActivity: Date.now() - lastActivityTime,
  };
}

/**
 * Extend session (manual extension)
 */
export function extendSession(config: SessionConfig = {}): void {
  updateActivity();
  resetSessionTimeout(
    config.timeout || SESSION_TIMEOUT,
    config.warningBefore || WARNING_BEFORE_TIMEOUT,
    config
  );
}

/**
 * End session manually
 */
export function endSession(): void {
  clearSessionTimers();
  clearAuth();
  window.location.href = '/login';
}

/**
 * Request notification permission for session warnings
 */
export async function requestNotificationPermission(): Promise<boolean> {
  if (!('Notification' in window)) {
    return false;
  }

  if (Notification.permission === 'granted') {
    return true;
  }

  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }

  return false;
}

/**
 * Check if session is about to expire
 */
export function isSessionExpiring(warningThreshold: number = WARNING_BEFORE_TIMEOUT): boolean {
  const timeSinceActivity = Date.now() - lastActivityTime;
  return timeSinceActivity > SESSION_TIMEOUT - warningThreshold;
}

/**
 * Get time until session expires (in seconds)
 */
export function getTimeUntilExpiry(): number {
  const timeSinceActivity = Date.now() - lastActivityTime;
  const timeRemaining = SESSION_TIMEOUT - timeSinceActivity;
  return Math.max(0, Math.floor(timeRemaining / 1000));
}
