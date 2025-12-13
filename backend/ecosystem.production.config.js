const path = require('path');

// Production paths - adjust for your Ubuntu server
const PROJECT_ROOT = process.env.APP_ROOT || '/var/www/healthtech-backend/backend';
const SERVICES_PATH = path.join(PROJECT_ROOT, 'services');

// Python path for production (use venv inside project)
const getPythonPath = () => {
  return process.env.PM2_PYTHON_PATH || path.join(PROJECT_ROOT, 'venv', 'bin', 'python');
};

// Service configuration generator for production
const createServiceConfig = (name, port, options = {}) => ({
  name: `prm-${name}`,
  script: getPythonPath(),
  args: `-m uvicorn services.${name}.main:app --host 0.0.0.0 --port ${port} --workers ${options.workers || 2}`,
  cwd: PROJECT_ROOT,
  watch: false,
  instances: options.instances || 1,
  exec_mode: 'fork',
  autorestart: true,
  max_restarts: 10,
  restart_delay: 3000,
  max_memory_restart: options.maxMemory || '1G',
  env_file: path.join(PROJECT_ROOT, '.env'),
  env: {
    NODE_ENV: 'production',
    PYTHONPATH: PROJECT_ROOT,
    PYTHONUNBUFFERED: '1',
    ENVIRONMENT: 'production',
    DEBUG: 'false',
    ...options.env
  },
  error_file: path.join(PROJECT_ROOT, 'logs', `${name}-error.log`),
  out_file: path.join(PROJECT_ROOT, 'logs', `${name}-out.log`),
  log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
  merge_logs: true,
  time: true,
  kill_timeout: 5000,
  listen_timeout: 10000,
  wait_ready: true,
});

module.exports = {
  apps: [
    // ============== CORE SERVICES ==============

    // PRM Service - Patient Relationship Management (Main service)
    createServiceConfig('prm-service', 8007, {
      workers: 4,
      maxMemory: '2G',
    }),

    // Identity Service - User management
    createServiceConfig('identity-service', 8000, {
      workers: 2,
      maxMemory: '1G',
    }),

    // Auth Service - Authentication
    createServiceConfig('auth-service', 8004, {
      workers: 2,
      maxMemory: '1G',
    }),

    // FHIR Service - FHIR compliance
    createServiceConfig('fhir-service', 8002, {
      workers: 2,
      maxMemory: '1G',
    }),

    // Consent Service - Consent management
    createServiceConfig('consent-service', 8003, {
      workers: 2,
      maxMemory: '512M',
    }),

    // ============== CLINICAL SERVICES ==============

    // Scheduling Service
    createServiceConfig('scheduling-service', 8005, {
      workers: 2,
      maxMemory: '1G',
    }),

    // Encounter Service
    createServiceConfig('encounter-service', 8006, {
      workers: 2,
      maxMemory: '1G',
    }),

    // Scribe Service - AI transcription
    createServiceConfig('scribe-service', 8008, {
      workers: 2,
      maxMemory: '2G',
    }),

    // ============== ADDITIONAL SERVICES (Add as needed) ==============

    // Bed Management Service
    createServiceConfig('bed-management-service', 8009, {
      workers: 1,
      maxMemory: '512M',
    }),

    // Admission Service
    createServiceConfig('admission-service', 8010, {
      workers: 1,
      maxMemory: '512M',
    }),

    // Analytics Hub Service
    createServiceConfig('analytics-hub-service', 8017, {
      workers: 2,
      maxMemory: '1G',
    }),
  ],
};
