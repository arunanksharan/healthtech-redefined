#!/bin/bash
# ============================================================================
# HealthTech Backend - Development Start Script
# ============================================================================
# Quick start script for local development
# Run from the backend directory: ./scripts/start-dev.sh
# ============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }
echo_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_ROOT="$(dirname "$SCRIPT_DIR")"
VENV_PATH="${BACKEND_ROOT}/venv"
PYTHON_VERSION=${PYTHON_VERSION:-3.11}

cd "${BACKEND_ROOT}"

echo "============================================================================"
echo "HealthTech Backend - Development Mode"
echo "============================================================================"

# Check if .env exists
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo_info "Creating .env from .env.example..."
        cp .env.example .env
        echo_warn "Please update .env with your configuration before running services"
    else
        echo_error ".env.example not found. Please create .env manually."
        exit 1
    fi
fi

# Create logs directory
mkdir -p logs

# Check virtual environment
echo_step "Checking virtual environment..."
if [ ! -d "${VENV_PATH}" ]; then
    echo_info "Creating virtual environment with Python ${PYTHON_VERSION}..."
    python${PYTHON_VERSION} -m venv "${VENV_PATH}" || python3 -m venv "${VENV_PATH}"
fi

# Activate virtual environment
source "${VENV_PATH}/bin/activate"
echo_info "Using Python: $(python --version)"
echo_info "Pip location: $(which pip)"

# Check if dependencies need to be installed
if [ ! -f "${VENV_PATH}/.deps_installed" ] || [ requirements.txt -nt "${VENV_PATH}/.deps_installed" ]; then
    echo_step "Installing dependencies..."
    pip install --upgrade pip --quiet

    # Try to install requirements, but continue even if some fail
    if pip install -r requirements.txt 2>&1; then
        touch "${VENV_PATH}/.deps_installed"
        echo_info "All dependencies installed successfully"
    else
        echo_warn "Some dependencies failed to install. Installing core dependencies..."
        # Install core dependencies that are essential for running
        pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic pydantic-settings \
                    python-dotenv loguru redis python-jose passlib httpx aiohttp \
                    python-multipart email-validator --quiet || true
        echo_warn "Partial dependencies installed. Some features may not work."
    fi
fi

# Run migrations
echo_step "Running database migrations..."
if command -v alembic &> /dev/null; then
    alembic upgrade head 2>&1 || echo_warn "Migrations failed. Make sure PostgreSQL is running and DATABASE_URL is configured."
else
    echo_warn "Alembic not found. Skipping migrations."
fi

# Set environment for PM2
export NODE_ENV=development
export PM2_PYTHON_PATH="${VENV_PATH}/bin/python"

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo_error "PM2 is not installed. Please install it with: npm install -g pm2"
    exit 1
fi

# Stop any existing services first
pm2 delete all 2>/dev/null || true

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
