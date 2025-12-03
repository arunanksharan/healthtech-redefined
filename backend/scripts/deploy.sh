#!/bin/bash
# ============================================================================
# HealthTech Backend - Deployment Script
# ============================================================================
# This script deploys/updates the backend application
# Run from the backend directory: ./scripts/deploy.sh [environment]
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }
echo_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# ============================================================================
# Configuration
# ============================================================================
ENVIRONMENT=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="${BACKEND_ROOT}/venv"
PYTHON_VERSION=${PYTHON_VERSION:-3.11}

echo "============================================================================"
echo "HealthTech Backend Deployment"
echo "============================================================================"
echo "Environment: ${ENVIRONMENT}"
echo "Backend Root: ${BACKEND_ROOT}"
echo "============================================================================"
echo ""

# ============================================================================
# Change to backend directory
# ============================================================================
cd "${BACKEND_ROOT}"

# ============================================================================
# Check if .env exists
# ============================================================================
echo_step "Checking environment configuration..."
if [ ! -f ".env" ]; then
    echo_error ".env file not found!"
    echo_info "Please copy .env.example to .env and configure it:"
    echo "  cp .env.example .env"
    echo "  vim .env"
    exit 1
fi
echo_info ".env file found"

# ============================================================================
# Create logs directory
# ============================================================================
echo_step "Creating logs directory..."
mkdir -p logs
echo_info "Logs directory ready"

# ============================================================================
# Setup Python virtual environment
# ============================================================================
echo_step "Setting up Python virtual environment..."
if [ ! -d "${VENV_PATH}" ]; then
    echo_info "Creating new virtual environment..."
    python${PYTHON_VERSION} -m venv "${VENV_PATH}"
else
    echo_info "Virtual environment exists"
fi

# Activate virtual environment
source "${VENV_PATH}/bin/activate"
echo_info "Python: $(python --version)"
echo_info "Pip: $(pip --version)"

# ============================================================================
# Upgrade pip and install dependencies
# ============================================================================
echo_step "Installing/updating dependencies..."
pip install --upgrade pip --quiet

# Install requirements with error handling
set +e  # Temporarily disable exit on error
pip install -r requirements.txt 2>&1
PIP_EXIT_CODE=$?
set -e  # Re-enable exit on error

if [ $PIP_EXIT_CODE -ne 0 ]; then
    echo_warn "Some dependencies failed to install. Installing core dependencies..."
    pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic pydantic-settings \
                python-dotenv loguru redis python-jose passlib httpx aiohttp \
                python-multipart email-validator confluent-kafka alembic --quiet
    echo_warn "Core dependencies installed. Some features may not work."
else
    echo_info "All dependencies installed successfully"
fi

# ============================================================================
# Run database migrations
# ============================================================================
echo_step "Running database migrations..."
if [ -f "alembic.ini" ]; then
    alembic upgrade head
    echo_info "Migrations completed"
else
    echo_warn "alembic.ini not found, skipping migrations"
fi

# ============================================================================
# Select ecosystem config based on environment
# ============================================================================
if [ "${ENVIRONMENT}" = "production" ]; then
    ECOSYSTEM_CONFIG="ecosystem.production.config.js"
else
    ECOSYSTEM_CONFIG="ecosystem.config.js"
fi

if [ ! -f "${ECOSYSTEM_CONFIG}" ]; then
    echo_error "${ECOSYSTEM_CONFIG} not found!"
    exit 1
fi

# ============================================================================
# Stop existing PM2 processes (if any)
# ============================================================================
echo_step "Checking existing PM2 processes..."
if pm2 list | grep -q "prm-"; then
    echo_info "Stopping existing services..."
    pm2 stop ${ECOSYSTEM_CONFIG} --silent || true
    pm2 delete ${ECOSYSTEM_CONFIG} --silent || true
fi

# ============================================================================
# Start services with PM2
# ============================================================================
echo_step "Starting services with PM2..."
export PM2_PYTHON_PATH="${VENV_PATH}/bin/python"
export APP_ROOT="${BACKEND_ROOT}"

pm2 start ${ECOSYSTEM_CONFIG} --env ${ENVIRONMENT}

# ============================================================================
# Save PM2 configuration
# ============================================================================
echo_step "Saving PM2 configuration..."
pm2 save

# ============================================================================
# Show status
# ============================================================================
echo ""
echo "============================================================================"
echo -e "${GREEN}Deployment Complete!${NC}"
echo "============================================================================"
echo ""
pm2 list

echo ""
echo "Useful commands:"
echo "  pm2 logs           - View all logs"
echo "  pm2 logs prm-*     - View specific service logs"
echo "  pm2 monit          - Monitor all services"
echo "  pm2 restart all    - Restart all services"
echo "  pm2 reload all     - Graceful reload all services"
echo "  pm2 stop all       - Stop all services"
echo ""
echo "============================================================================"
