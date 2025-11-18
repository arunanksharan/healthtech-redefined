#!/bin/bash

# AI-Native Healthcare Platform - Setup Script
# This script sets up the complete development environment

set -e  # Exit on error

echo "🏥 AI-Native Healthcare Platform - Setup"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check prerequisites
print_info "Checking prerequisites..."

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
else
    print_error "Python 3.11+ is required but not found"
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    print_success "Node.js $NODE_VERSION found"
else
    print_error "Node.js 18+ is required but not found"
    exit 1
fi

# Check Docker
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
    print_success "Docker $DOCKER_VERSION found"
else
    print_error "Docker is required but not found"
    exit 1
fi

# Check Docker Compose
if command -v docker-compose &> /dev/null; then
    print_success "Docker Compose found"
else
    print_error "Docker Compose is required but not found"
    exit 1
fi

echo ""
print_info "Setting up backend..."

# Create Python virtual environment
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Python virtual environment created"
else
    print_info "Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
print_info "Installing Python dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
print_success "Python dependencies installed"

cd ..

echo ""
print_info "Setting up frontend..."

# Install Node dependencies
if [ ! -d "node_modules" ]; then
    npm install
    print_success "Node dependencies installed"
else
    print_info "Node modules already exist"
fi

echo ""
print_info "Starting infrastructure services..."

# Start Docker services
docker-compose up -d postgres redis kafka zookeeper

# Wait for services to be healthy
print_info "Waiting for services to be healthy..."
sleep 10

# Check PostgreSQL
if docker exec healthtech-postgres pg_isready -U postgres > /dev/null 2>&1; then
    print_success "PostgreSQL is ready"
else
    print_error "PostgreSQL failed to start"
    exit 1
fi

# Check Redis
if docker exec healthtech-redis redis-cli ping > /dev/null 2>&1; then
    print_success "Redis is ready"
else
    print_error "Redis failed to start"
    exit 1
fi

print_success "All infrastructure services are running"

echo ""
print_info "Setting up database..."

# Initialize Alembic if not already done
cd backend
if [ ! -f "alembic.ini" ]; then
    print_info "Initializing Alembic..."
    alembic init migrations
    print_success "Alembic initialized"
else
    print_info "Alembic already initialized"
fi

# Create initial migration if needed
if [ ! -d "migrations/versions" ] || [ -z "$(ls -A migrations/versions 2>/dev/null)" ]; then
    print_info "Creating initial migration..."
    alembic revision --autogenerate -m "Initial schema"
    print_success "Initial migration created"
fi

# Run migrations
print_info "Running database migrations..."
alembic upgrade head
print_success "Database migrations complete"

cd ..

echo ""
echo "========================================="
print_success "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Start backend services:"
echo "   docker-compose up identity-service fhir-service consent-service auth-service"
echo ""
echo "2. Start frontend (in new terminal):"
echo "   cd frontend/apps/admin-console"
echo "   npm run dev"
echo ""
echo "3. Access services:"
echo "   - Admin Console: http://localhost:3000"
echo "   - Identity API: http://localhost:8001/docs"
echo "   - FHIR API: http://localhost:8002/docs"
echo "   - Consent API: http://localhost:8003/docs"
echo "   - Auth API: http://localhost:8004/docs"
echo "   - Grafana: http://localhost:3001 (admin/admin)"
echo "   - PgAdmin: http://localhost:5050 (admin@healthtech.com/admin)"
echo ""
echo "For more information, see:"
echo "   - README.md"
echo "   - DEVELOPER_QUICK_START_GUIDE.md"
echo "   - NEXT_STEPS.md"
echo ""
