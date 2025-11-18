/**
 * Health Check API Endpoint
 * Used by Docker, Kubernetes, load balancers, and monitoring systems
 */

import { NextResponse } from 'next/server';

// Health check configuration
const HEALTH_CHECK_TIMEOUT = 5000; // 5 seconds
const REQUIRED_ENV_VARS = [
  'NEXT_PUBLIC_API_URL',
  'JWT_SECRET',
];

interface HealthCheckResult {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  uptime: number;
  version: string;
  checks: {
    name: string;
    status: 'pass' | 'fail' | 'warn';
    message?: string;
    responseTime?: number;
  }[];
}

/**
 * Check if required environment variables are set
 */
function checkEnvironmentVariables(): {
  status: 'pass' | 'fail';
  message?: string;
} {
  const missing = REQUIRED_ENV_VARS.filter((key) => !process.env[key]);

  if (missing.length > 0) {
    return {
      status: 'fail',
      message: `Missing required environment variables: ${missing.join(', ')}`,
    };
  }

  return { status: 'pass' };
}

/**
 * Check API backend connectivity
 */
async function checkBackendAPI(): Promise<{
  status: 'pass' | 'fail' | 'warn';
  message?: string;
  responseTime?: number;
}> {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL;

  if (!apiUrl) {
    return {
      status: 'warn',
      message: 'API URL not configured',
    };
  }

  const startTime = Date.now();

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), HEALTH_CHECK_TIMEOUT);

    const response = await fetch(`${apiUrl}/health`, {
      signal: controller.signal,
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    clearTimeout(timeoutId);
    const responseTime = Date.now() - startTime;

    if (response.ok) {
      return {
        status: 'pass',
        responseTime,
      };
    } else {
      return {
        status: 'fail',
        message: `API returned status ${response.status}`,
        responseTime,
      };
    }
  } catch (error) {
    const responseTime = Date.now() - startTime;

    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        return {
          status: 'fail',
          message: 'API health check timed out',
          responseTime: HEALTH_CHECK_TIMEOUT,
        };
      }

      return {
        status: 'fail',
        message: `API health check failed: ${error.message}`,
        responseTime,
      };
    }

    return {
      status: 'fail',
      message: 'API health check failed: Unknown error',
      responseTime,
    };
  }
}

/**
 * Check memory usage
 */
function checkMemoryUsage(): {
  status: 'pass' | 'warn' | 'fail';
  message?: string;
} {
  if (typeof process === 'undefined') {
    return { status: 'warn', message: 'Memory check not available' };
  }

  const usage = process.memoryUsage();
  const usedMB = Math.round(usage.heapUsed / 1024 / 1024);
  const totalMB = Math.round(usage.heapTotal / 1024 / 1024);
  const percentUsed = (usedMB / totalMB) * 100;

  if (percentUsed > 90) {
    return {
      status: 'fail',
      message: `Memory usage critical: ${usedMB}MB / ${totalMB}MB (${percentUsed.toFixed(1)}%)`,
    };
  }

  if (percentUsed > 75) {
    return {
      status: 'warn',
      message: `Memory usage high: ${usedMB}MB / ${totalMB}MB (${percentUsed.toFixed(1)}%)`,
    };
  }

  return {
    status: 'pass',
    message: `Memory usage normal: ${usedMB}MB / ${totalMB}MB (${percentUsed.toFixed(1)}%)`,
  };
}

/**
 * GET /api/health
 * Returns health check status
 */
export async function GET() {
  const startTime = Date.now();

  // Perform health checks
  const checks = [
    {
      name: 'environment',
      ...checkEnvironmentVariables(),
    },
    {
      name: 'backend_api',
      ...(await checkBackendAPI()),
    },
    {
      name: 'memory',
      ...checkMemoryUsage(),
    },
  ];

  // Determine overall status
  const hasFailures = checks.some((check) => check.status === 'fail');
  const hasWarnings = checks.some((check) => check.status === 'warn');

  let overallStatus: 'healthy' | 'degraded' | 'unhealthy';
  if (hasFailures) {
    overallStatus = 'unhealthy';
  } else if (hasWarnings) {
    overallStatus = 'degraded';
  } else {
    overallStatus = 'healthy';
  }

  // Build response
  const result: HealthCheckResult = {
    status: overallStatus,
    timestamp: new Date().toISOString(),
    uptime: process.uptime ? process.uptime() : 0,
    version: process.env.npm_package_version || '1.0.0',
    checks,
  };

  // Determine HTTP status code
  let statusCode = 200;
  if (overallStatus === 'unhealthy') {
    statusCode = 503; // Service Unavailable
  } else if (overallStatus === 'degraded') {
    statusCode = 200; // Still functional, but degraded
  }

  const responseTime = Date.now() - startTime;

  return NextResponse.json(
    {
      ...result,
      responseTime,
    },
    {
      status: statusCode,
      headers: {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Content-Type': 'application/json',
      },
    }
  );
}

/**
 * HEAD /api/health
 * Lightweight health check (just returns status code)
 */
export async function HEAD() {
  // Quick check - just verify environment variables
  const envCheck = checkEnvironmentVariables();

  if (envCheck.status === 'fail') {
    return new Response(null, { status: 503 });
  }

  return new Response(null, {
    status: 200,
    headers: {
      'Cache-Control': 'no-cache, no-store, must-revalidate',
    },
  });
}
