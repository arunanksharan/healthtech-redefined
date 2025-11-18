/**
 * Client-side rate limiting
 * Prevents brute force attacks and excessive API calls
 */

interface RateLimitConfig {
  maxAttempts: number;
  windowMs: number;
  blockDurationMs?: number;
}

interface RateLimitEntry {
  attempts: number;
  firstAttempt: number;
  blockedUntil?: number;
}

const rateLimitStore = new Map<string, RateLimitEntry>();

/**
 * Check if action is rate limited
 */
export function isRateLimited(
  key: string,
  config: RateLimitConfig = { maxAttempts: 5, windowMs: 60000 }
): boolean {
  const now = Date.now();
  const entry = rateLimitStore.get(key);

  if (!entry) {
    // First attempt
    rateLimitStore.set(key, {
      attempts: 1,
      firstAttempt: now,
    });
    return false;
  }

  // Check if blocked
  if (entry.blockedUntil && now < entry.blockedUntil) {
    return true;
  }

  // Check if window expired
  if (now - entry.firstAttempt > config.windowMs) {
    // Reset window
    rateLimitStore.set(key, {
      attempts: 1,
      firstAttempt: now,
    });
    return false;
  }

  // Increment attempts
  entry.attempts++;

  // Check if limit exceeded
  if (entry.attempts > config.maxAttempts) {
    // Block for duration
    entry.blockedUntil = now + (config.blockDurationMs || config.windowMs * 2);
    return true;
  }

  return false;
}

/**
 * Reset rate limit for a key
 */
export function resetRateLimit(key: string): void {
  rateLimitStore.delete(key);
}

/**
 * Get remaining attempts
 */
export function getRemainingAttempts(
  key: string,
  maxAttempts: number = 5
): number {
  const entry = rateLimitStore.get(key);
  if (!entry) return maxAttempts;
  return Math.max(0, maxAttempts - entry.attempts);
}

/**
 * Get time until unblocked (in ms)
 */
export function getBlockedTime(key: string): number {
  const entry = rateLimitStore.get(key);
  if (!entry || !entry.blockedUntil) return 0;

  const remaining = entry.blockedUntil - Date.now();
  return Math.max(0, remaining);
}

/**
 * Rate limiter for login attempts
 */
export const loginRateLimiter = {
  check: (email: string): boolean => {
    return isRateLimited(`login:${email}`, {
      maxAttempts: 5,
      windowMs: 15 * 60 * 1000, // 15 minutes
      blockDurationMs: 30 * 60 * 1000, // 30 minutes
    });
  },

  reset: (email: string): void => {
    resetRateLimit(`login:${email}`);
  },

  getRemaining: (email: string): number => {
    return getRemainingAttempts(`login:${email}`, 5);
  },

  getBlockedTime: (email: string): number => {
    return getBlockedTime(`login:${email}`);
  },
};

/**
 * Rate limiter for API calls
 */
export const apiRateLimiter = {
  check: (endpoint: string): boolean => {
    return isRateLimited(`api:${endpoint}`, {
      maxAttempts: 100,
      windowMs: 60 * 1000, // 1 minute
    });
  },

  reset: (endpoint: string): void => {
    resetRateLimit(`api:${endpoint}`);
  },
};

/**
 * Rate limiter for password reset
 */
export const passwordResetRateLimiter = {
  check: (email: string): boolean => {
    return isRateLimited(`password-reset:${email}`, {
      maxAttempts: 3,
      windowMs: 60 * 60 * 1000, // 1 hour
      blockDurationMs: 24 * 60 * 60 * 1000, // 24 hours
    });
  },

  reset: (email: string): void => {
    resetRateLimit(`password-reset:${email}`);
  },

  getRemaining: (email: string): number => {
    return getRemainingAttempts(`password-reset:${email}`, 3);
  },
};

/**
 * Cleanup old entries (call periodically)
 */
export function cleanupRateLimits(): void {
  const now = Date.now();

  for (const [key, entry] of rateLimitStore.entries()) {
    // Remove if window expired and not blocked
    const windowExpired = now - entry.firstAttempt > 60 * 60 * 1000; // 1 hour
    const notBlocked = !entry.blockedUntil || now > entry.blockedUntil;

    if (windowExpired && notBlocked) {
      rateLimitStore.delete(key);
    }
  }
}

// Cleanup every 5 minutes
if (typeof window !== 'undefined') {
  setInterval(cleanupRateLimits, 5 * 60 * 1000);
}
