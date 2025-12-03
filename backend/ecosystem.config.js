const path = require('path');

// Base paths
const PROJECT_ROOT = __dirname;
const SERVICES_PATH = path.join(PROJECT_ROOT, 'services');

// Python interpreter path (relative to project)
// Development: Use local venv
// Production: Override via PM2_PYTHON_PATH env var
const getPythonPath = () => {
  if (process.env.PM2_PYTHON_PATH) {
    return process.env.PM2_PYTHON_PATH;
  }
  // Default to local venv
  return path.join(PROJECT_ROOT, 'venv', 'bin', 'python');
};

// Service configuration generator
const createServiceConfig = (name, port, options = {}) => ({
  name: `prm-${name}`,
  script: getPythonPath(),
  args: `-m uvicorn services.${name}.main:app --host 0.0.0.0 --port ${port}`,
  cwd: PROJECT_ROOT,
  watch: options.watch || false,
  ignore_watch: ['venv', '__pycache__', '*.pyc', 'logs', 'alembic'],
  instances: options.instances || 1,
  exec_mode: options.instances > 1 ? 'cluster' : 'fork',
  autorestart: true,
  max_restarts: 10,
  restart_delay: 1000,
  max_memory_restart: options.maxMemory || '512M',
  env_file: path.join(PROJECT_ROOT, '.env'),
  env: {
    NODE_ENV: 'development',
    PYTHONPATH: PROJECT_ROOT,
    PYTHONUNBUFFERED: '1',
    ...options.env
  },
  error_file: path.join(PROJECT_ROOT, 'logs', `${name}-error.log`),
  out_file: path.join(PROJECT_ROOT, 'logs', `${name}-out.log`),
  log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
  merge_logs: true,
});

module.exports = {
  apps: [
    // ============== CORE SERVICES ==============

    // PRM Service - Patient Relationship Management (Main service)
    createServiceConfig('prm-service', 8007, {
      watch: process.env.NODE_ENV !== 'production',
      maxMemory: '1G',
    }),

    // Identity Service - User management
    createServiceConfig('identity-service', 8000, {
      watch: process.env.NODE_ENV !== 'production',
    }),

    // Auth Service - Authentication
    createServiceConfig('auth-service', 8004, {
      watch: process.env.NODE_ENV !== 'production',
    }),

    // FHIR Service - FHIR compliance
    createServiceConfig('fhir-service', 8002, {
      watch: process.env.NODE_ENV !== 'production',
    }),

    // Consent Service - Consent management
    createServiceConfig('consent-service', 8003, {
      watch: process.env.NODE_ENV !== 'production',
    }),

    // ============== CLINICAL SERVICES ==============

    // Scheduling Service
    createServiceConfig('scheduling-service', 8005, {
      watch: process.env.NODE_ENV !== 'production',
    }),

    // Encounter Service
    createServiceConfig('encounter-service', 8006, {
      watch: process.env.NODE_ENV !== 'production',
    }),

    // Scribe Service - AI transcription
    createServiceConfig('scribe-service', 8008, {
      watch: process.env.NODE_ENV !== 'production',
      maxMemory: '1G',
    }),
  ],

  // Deployment configuration
  deploy: {
    production: {
      user: 'deploy',
      host: ['your-production-server.com'],
      ref: 'origin/main',
      repo: 'git@github.com:your-org/healthtech-redefined.git',
      path: '/var/www/healthtech-backend',
      'pre-deploy': 'git fetch --all',
      'post-deploy': 'cd backend && source venv/bin/activate && pip install -r requirements.txt && alembic upgrade head && pm2 reload ecosystem.config.js --env production',
      env: {
        NODE_ENV: 'production',
      },
    },
    staging: {
      user: 'deploy',
      host: ['your-staging-server.com'],
      ref: 'origin/develop',
      repo: 'git@github.com:your-org/healthtech-redefined.git',
      path: '/var/www/healthtech-backend-staging',
      'pre-deploy': 'git fetch --all',
      'post-deploy': 'cd backend && source venv/bin/activate && pip install -r requirements.txt && alembic upgrade head && pm2 reload ecosystem.config.js --env staging',
      env: {
        NODE_ENV: 'staging',
      },
    },
  },
};
