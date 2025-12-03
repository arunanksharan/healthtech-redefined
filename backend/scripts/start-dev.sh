#!/bin/bash
# ============================================================================
# HealthTech Backend - Development Start Script
# ============================================================================
# Quick start script for local development
# Run from the backend directory: ./scripts/start-dev.sh
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="${BACKEND_ROOT}/venv"

cd "${BACKEND_ROOT}"

echo "============================================================================"
echo "HealthTech Backend - Development Mode"
echo "============================================================================"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo_info "Creating .env from .env.example..."
    cp .env.example .env
    echo "Please update .env with your configuration"
fi

# Create logs directory
mkdir -p logs

# Check virtual environment
echo_step "Checking virtual environment..."
if [ ! -d "${VENV_PATH}" ]; then
    echo_info "Creating virtual environment..."
    python3 -m venv "${VENV_PATH}"
fi

# Activate and install dependencies
source "${VENV_PATH}/bin/activate"
echo_info "Using Python: $(python --version)"

# Check if dependencies need to be installed
if [ ! -f "${VENV_PATH}/.deps_installed" ] || [ requirements.txt -nt "${VENV_PATH}/.deps_installed" ]; then
    echo_step "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch "${VENV_PATH}/.deps_installed"
fi

# Run migrations
echo_step "Running database migrations..."
alembic upgrade head || echo "Warning: Migrations failed. Make sure PostgreSQL is running."

# Set environment for PM2
export NODE_ENV=development
export PM2_PYTHON_PATH="${VENV_PATH}/bin/python"

# Start with PM2
echo_step "Starting services with PM2..."
pm2 start ecosystem.config.js --env development

echo ""
echo "============================================================================"
echo -e "${GREEN}Development server started!${NC}"
echo "============================================================================"
echo ""
pm2 list

echo ""
echo "Services running at:"
echo "  - PRM Service:      http://localhost:8007/docs"
echo "  - Identity Service: http://localhost:8000/docs"
echo "  - Auth Service:     http://localhost:8004/docs"
echo "  - FHIR Service:     http://localhost:8002/docs"
echo "  - Consent Service:  http://localhost:8003/docs"
echo ""
echo "Commands:"
echo "  pm2 logs -f        - Follow all logs"
echo "  pm2 monit          - Interactive monitor"
echo "  pm2 stop all       - Stop all services"
echo "  pm2 restart all    - Restart all services"
echo ""
