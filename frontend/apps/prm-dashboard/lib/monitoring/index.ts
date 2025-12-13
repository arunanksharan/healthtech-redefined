/**
 * Monitoring and Observability
 * Centralized monitoring configuration for production
 */

// Sentry Configuration
export const initSentry = () => {
  if (process.env.NEXT_PUBLIC_SENTRY_DSN && typeof window !== 'undefined') {
    // Dynamically import Sentry to reduce initial bundle size
    import('@sentry/nextjs').then((Sentry) => {
      Sentry.init({
        dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
        environment: process.env.NODE_ENV || 'development',
        tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.1 : 1.0,
        replaysSessionSampleRate: 0.1,
        replaysOnErrorSampleRate: 1.0,

        beforeSend(event, hint) {
          // Filter out specific errors
          const error = hint.originalException;

          if (error instanceof Error) {
            // Ignore specific error types
            if (error.message.includes('ResizeObserver loop')) {
              return null; // Don't send to Sentry
            }
          }

          // Sanitize PHI from error data
          if (event.extra) {
            event.extra = sanitizePHI(event.extra);
          }

          return event;
        },
      });
    });
  }
};

// Analytics Configuration
export const initAnalytics = () => {
  if (process.env.NEXT_PUBLIC_ANALYTICS_ID && typeof window !== 'undefined') {
    // Google Analytics
    const script = document.createElement('script');
    script.src = `https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_ANALYTICS_ID}`;
    script.async = true;
    document.head.appendChild(script);

    window.dataLayer = window.dataLayer || [];
    function gtag(...args: any[]) {
      window.dataLayer.push(args);
    }
    gtag('js', new Date());
    gtag('config', process.env.NEXT_PUBLIC_ANALYTICS_ID, {
      anonymize_ip: true, // HIPAA compliance
      page_path: window.location.pathname,
    });
  }
};

// Performance Monitoring
export const trackPerformance = () => {
  if (typeof window === 'undefined') return;

  // Web Vitals (using web-vitals 4.x API - onFID replaced by onINP)
  import('web-vitals').then(({ onCLS, onINP, onFCP, onLCP, onTTFB }) => {
    onCLS(sendToAnalytics);
    onINP(sendToAnalytics);
    onFCP(sendToAnalytics);
    onLCP(sendToAnalytics);
    onTTFB(sendToAnalytics);
  });
};

function sendToAnalytics(metric: any) {
  // Send to analytics service
  if (window.gtag) {
    window.gtag('event', metric.name, {
      value: Math.round(metric.name === 'CLS' ? metric.value * 1000 : metric.value),
      event_category: 'Web Vitals',
      event_label: metric.id,
      non_interaction: true,
    });
  }

  // Also log in development
  if (process.env.NODE_ENV === 'development') {
    console.log('[Performance]', metric.name, metric.value);
  }
}

// Sanitize PHI from data before sending to monitoring services
function sanitizePHI(data: any): any {
  const piiFields = [
    'email',
    'phone',
    'ssn',
    'patient_id',
    'date_of_birth',
    'address',
    'name',
    'medical_record_number',
  ];

  if (Array.isArray(data)) {
    return data.map(sanitizePHI);
  }

  if (data && typeof data === 'object') {
    const sanitized: any = {};
    for (const key in data) {
      if (piiFields.some((field) => key.toLowerCase().includes(field))) {
        sanitized[key] = '[REDACTED]';
      } else {
        sanitized[key] = sanitizePHI(data[key]);
      }
    }
    return sanitized;
  }

  return data;
}

// Custom event tracking
export const trackEvent = (eventName: string, properties?: Record<string, any>) => {
  // Sanitize properties
  const sanitizedProperties = properties ? sanitizePHI(properties) : {};

  // Send to analytics
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', eventName, sanitizedProperties);
  }

  // Log in development
  if (process.env.NODE_ENV === 'development') {
    console.log('[Event]', eventName, sanitizedProperties);
  }
};

// Error tracking
export const trackError = (error: Error, context?: Record<string, any>) => {
  // Sanitize context
  const sanitizedContext = context ? sanitizePHI(context) : {};

  // Send to Sentry
  if (process.env.NEXT_PUBLIC_SENTRY_DSN) {
    import('@sentry/nextjs').then((Sentry) => {
      Sentry.captureException(error, {
        extra: sanitizedContext,
      });
    });
  }

  // Log in development
  if (process.env.NODE_ENV === 'development') {
    console.error('[Error]', error, sanitizedContext);
  }
};

// API call tracking
export const trackAPICall = (endpoint: string, method: string, duration: number, status: number) => {
  trackEvent('api_call', {
    endpoint: endpoint.replace(/\/\d+/g, '/:id'), // Replace IDs with :id
    method,
    duration,
    status,
  });

  // Track slow API calls
  if (duration > 2000) {
    trackEvent('slow_api_call', {
      endpoint: endpoint.replace(/\/\d+/g, '/:id'),
      duration,
    });
  }

  // Track failed API calls
  if (status >= 400) {
    trackEvent('api_error', {
      endpoint: endpoint.replace(/\/\d+/g, '/:id'),
      status,
    });
  }
};

// User action tracking
export const trackUserAction = (action: string, details?: Record<string, any>) => {
  trackEvent('user_action', {
    action,
    ...sanitizePHI(details || {}),
  });
};

// Page view tracking
export const trackPageView = (path: string) => {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('config', process.env.NEXT_PUBLIC_ANALYTICS_ID, {
      page_path: path,
    });
  }
};

// Initialize all monitoring
export const initMonitoring = () => {
  if (process.env.NODE_ENV === 'production') {
    initSentry();
    initAnalytics();
    trackPerformance();
  }
};

// Type declarations
declare global {
  interface Window {
    dataLayer: any[];
    gtag: (...args: any[]) => void;
  }
}
