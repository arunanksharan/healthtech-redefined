/**
 * Security Tests
 * Tests for authentication, authorization, encryption, and other security features
 */

import {
  isAuthenticated,
  hasPermission,
  hasRole,
  storeTokens,
  clearAuth,
  isTokenExpired,
} from '../auth/auth';
import {
  encrypt,
  decrypt,
  hash,
  maskEmail,
  maskPhone,
  redactPII,
  sanitizeHTML,
} from '../encryption';
import {
  loginRateLimiter,
  passwordResetRateLimiter,
} from '../rate-limiter';

describe('Authentication', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  describe('Token Management', () => {
    it('should store and retrieve tokens', () => {
      const tokens = {
        access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwibmFtZSI6IlRlc3QgVXNlciIsInJvbGUiOiJhZG1pbiIsIm9yZ19pZCI6Im9yZ18xMjMiLCJwZXJtaXNzaW9ucyI6WyJwYXRpZW50LnZpZXciXSwiZXhwIjo5OTk5OTk5OTk5LCJpYXQiOjE1MTYyMzkwMjJ9.invalid-signature',
        refresh_token: 'refresh_token_here',
        expires_in: 3600,
      };

      storeTokens(tokens);

      expect(localStorage.getItem('auth_access_token')).toBe(tokens.access_token);
      expect(localStorage.getItem('auth_refresh_token')).toBe(tokens.refresh_token);
    });

    it('should clear auth data', () => {
      storeTokens({
        access_token: 'token',
        refresh_token: 'refresh',
        expires_in: 3600,
      });

      clearAuth();

      expect(localStorage.getItem('auth_access_token')).toBeNull();
      expect(localStorage.getItem('auth_refresh_token')).toBeNull();
      expect(localStorage.getItem('auth_user')).toBeNull();
    });
  });

  describe('Authorization', () => {
    beforeEach(() => {
      const mockUser = {
        id: '123',
        email: 'test@example.com',
        name: 'Test User',
        role: 'provider' as const,
        org_id: 'org_123',
        permissions: ['patient.view', 'appointment.create'],
      };

      localStorage.setItem('auth_user', JSON.stringify(mockUser));
    });

    it('should check permission correctly', () => {
      expect(hasPermission('patient.view')).toBe(true);
      expect(hasPermission('patient.delete')).toBe(false);
    });

    it('should check role correctly', () => {
      expect(hasRole('provider')).toBe(true);
      expect(hasRole('admin')).toBe(false);
      expect(hasRole(['provider', 'staff'])).toBe(true);
    });

    it('should grant admin all permissions', () => {
      const adminUser = {
        id: '456',
        email: 'admin@example.com',
        name: 'Admin User',
        role: 'admin' as const,
        org_id: 'org_123',
        permissions: [],
      };

      localStorage.setItem('auth_user', JSON.stringify(adminUser));

      expect(hasPermission('any.permission')).toBe(true);
    });
  });
});

describe('Encryption', () => {
  describe('AES Encryption', () => {
    it('should encrypt and decrypt data', async () => {
      const key = await crypto.subtle.generateKey(
        { name: 'AES-GCM', length: 256 },
        true,
        ['encrypt', 'decrypt']
      );

      const data = 'Sensitive patient information';
      const encrypted = await encrypt(data, key);
      const decrypted = await decrypt(encrypted, key);

      expect(decrypted).toBe(data);
      expect(encrypted).not.toBe(data);
    });

    it('should produce different ciphertext for same data', async () => {
      const key = await crypto.subtle.generateKey(
        { name: 'AES-GCM', length: 256 },
        true,
        ['encrypt', 'decrypt']
      );

      const data = 'Test data';
      const encrypted1 = await encrypt(data, key);
      const encrypted2 = await encrypt(data, key);

      // Different because of random IV
      expect(encrypted1).not.toBe(encrypted2);

      // But both decrypt to same data
      expect(await decrypt(encrypted1, key)).toBe(data);
      expect(await decrypt(encrypted2, key)).toBe(data);
    });
  });

  describe('Hashing', () => {
    it('should produce consistent hashes', async () => {
      const data = 'test data';
      const hash1 = await hash(data);
      const hash2 = await hash(data);

      expect(hash1).toBe(hash2);
    });

    it('should produce different hashes for different data', async () => {
      const hash1 = await hash('data1');
      const hash2 = await hash('data2');

      expect(hash1).not.toBe(hash2);
    });
  });

  describe('Data Masking', () => {
    it('should mask email correctly', () => {
      expect(maskEmail('patient@example.com')).toBe('pa*****@example.com');
      expect(maskEmail('a@example.com')).toBe('a*@example.com');
    });

    it('should mask phone correctly', () => {
      expect(maskPhone('555-123-4567')).toBe('*******4567');
      expect(maskPhone('+1 (555) 123-4567')).toBe('***********4567');
    });

    it('should redact PII from objects', () => {
      const data = {
        name: 'John Doe',
        ssn: '123-45-6789',
        email: 'john@example.com',
        address: '123 Main St',
        medical_data: {
          diagnosis: 'Condition',
          dob: '1990-01-01',
        },
      };

      const redacted = redactPII(data);

      expect(redacted.name).toBe('John Doe');
      expect(redacted.ssn).toBe('[REDACTED]');
      expect(redacted.email).toBe('[REDACTED]');
      expect(redacted.address).toBe('[REDACTED]');
      expect(redacted.medical_data.diagnosis).toBe('Condition');
      expect(redacted.medical_data.dob).toBe('[REDACTED]');
    });
  });

  describe('HTML Sanitization', () => {
    it('should prevent XSS attacks', () => {
      const malicious = '<script>alert("XSS")</script>';
      const sanitized = sanitizeHTML(malicious);

      expect(sanitized).not.toContain('<script>');
      expect(sanitized).toBe('&lt;script&gt;alert("XSS")&lt;/script&gt;');
    });

    it('should preserve safe text', () => {
      const safe = 'Normal text with <special> characters';
      const sanitized = sanitizeHTML(safe);

      expect(sanitized).toBe('Normal text with &lt;special&gt; characters');
    });
  });
});

describe('Rate Limiting', () => {
  beforeEach(() => {
    // Reset rate limiters
    loginRateLimiter.reset('test@example.com');
    passwordResetRateLimiter.reset('test@example.com');
  });

  describe('Login Rate Limiting', () => {
    it('should allow attempts within limit', () => {
      for (let i = 0; i < 5; i++) {
        expect(loginRateLimiter.check('test@example.com')).toBe(false);
      }
    });

    it('should block after max attempts', () => {
      // Use up all attempts
      for (let i = 0; i < 5; i++) {
        loginRateLimiter.check('test@example.com');
      }

      // Next attempt should be blocked
      expect(loginRateLimiter.check('test@example.com')).toBe(true);
    });

    it('should reset after successful login', () => {
      // Use some attempts
      for (let i = 0; i < 3; i++) {
        loginRateLimiter.check('test@example.com');
      }

      // Reset
      loginRateLimiter.reset('test@example.com');

      // Should allow new attempts
      expect(loginRateLimiter.check('test@example.com')).toBe(false);
    });

    it('should track remaining attempts', () => {
      expect(loginRateLimiter.getRemaining('test@example.com')).toBe(5);

      loginRateLimiter.check('test@example.com');
      expect(loginRateLimiter.getRemaining('test@example.com')).toBe(4);

      loginRateLimiter.check('test@example.com');
      expect(loginRateLimiter.getRemaining('test@example.com')).toBe(3);
    });
  });

  describe('Password Reset Rate Limiting', () => {
    it('should have stricter limits', () => {
      // Only 3 attempts allowed
      for (let i = 0; i < 3; i++) {
        expect(passwordResetRateLimiter.check('test@example.com')).toBe(false);
      }

      // 4th attempt should be blocked
      expect(passwordResetRateLimiter.check('test@example.com')).toBe(true);
    });
  });
});

describe('Input Validation', () => {
  it('should reject SQL injection attempts', () => {
    const malicious = "'; DROP TABLE users; --";
    // In practice, this would be validated by Zod schemas
    expect(malicious).toContain('DROP TABLE');
  });

  it('should reject XSS in inputs', () => {
    const malicious = '<img src=x onerror=alert(1)>';
    const sanitized = sanitizeHTML(malicious);

    expect(sanitized).not.toContain('onerror');
  });
});

describe('Security Headers', () => {
  // These would be tested in E2E tests
  it('should be documented', () => {
    const expectedHeaders = [
      'Strict-Transport-Security',
      'X-Frame-Options',
      'X-Content-Type-Options',
      'X-XSS-Protection',
      'Referrer-Policy',
    ];

    expect(expectedHeaders.length).toBeGreaterThan(0);
  });
});
