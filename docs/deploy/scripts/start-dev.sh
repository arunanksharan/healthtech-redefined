#!/bin/bash
#
# HealthTech Platform - Development Startup Script
#
# This script starts all infrastructure services and prepares the development environment.
# Usage: ./docs/deploy/scripts/start-dev.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           HealthTech PRM Platform - Dev Setup                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

check_command() {
    if command -v $1 &> /dev/null; then
        echo -e "  ✅ $1 found"
        return 0
    else
        echo -e "  ${RED}❌ $1 not found${NC}"
        return 1
    fi
}

check_command docker || exit 1
check_command docker compose || { check_command docker-compose || exit 1; }
check_command python3 || exit 1
check_command node || exit 1
check_command npm || exit 1

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "\n${YELLOW}Project root: $PROJECT_ROOT${NC}"

# Wait for service to be ready
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=${3:-30}
    local attempt=1

    echo -n "  Waiting for $name"
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e " ${GREEN}Ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo -e " ${RED}Timeout!${NC}"
    return 1
}

wait_for_port() {
    local port=$1
    local name=$2
    local max_attempts=${3:-30}
    local attempt=1

    echo -n "  Waiting for $name (port $port)"
    while [ $attempt -le $max_attempts ]; do
        if nc -z localhost $port 2>/dev/null; then
            echo -e " ${GREEN}Ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo -e " ${RED}Timeout!${NC}"
    return 1
}

# Step 1: Check for environment files
echo -e "\n${BLUE}Step 1: Checking environment files...${NC}"

if [ ! -f "backend/.env" ]; then
    echo -e "  ${YELLOW}Creating backend/.env from template...${NC}"
    if [ -f "docs/deploy/env-templates/.env.backend.example" ]; then
        cp docs/deploy/env-templates/.env.backend.example backend/.env
        echo -e "  ${GREEN}Created backend/.env${NC}"
        echo -e "  ${YELLOW}⚠️  Please update backend/.env with your API keys${NC}"
    else
        echo -e "  ${RED}Template not found. Please create backend/.env manually.${NC}"
    fi
else
    echo -e "  ✅ backend/.env exists"
fi

if [ ! -f "frontend/apps/prm-dashboard/.env.local" ]; then
    echo -e "  ${YELLOW}Creating frontend/.env.local from template...${NC}"
    if [ -f "docs/deploy/env-templates/.env.frontend.example" ]; then
        cp docs/deploy/env-templates/.env.frontend.example frontend/apps/prm-dashboard/.env.local
        echo -e "  ${GREEN}Created frontend/.env.local${NC}"
        echo -e "  ${YELLOW}⚠️  Please update frontend/.env.local with your API keys${NC}"
    else
        echo -e "  ${RED}Template not found. Please create frontend/.env.local manually.${NC}"
    fi
else
    echo -e "  ✅ frontend/.env.local exists"
fi

# Step 2: Start infrastructure
echo -e "\n${BLUE}Step 2: Starting infrastructure services...${NC}"

echo "  Starting PostgreSQL, Redis, Zookeeper..."
docker compose up -d postgres redis zookeeper

wait_for_port 5432 "PostgreSQL" 30
wait_for_port 6379 "Redis" 15
wait_for_port 2181 "Zookeeper" 30

# Step 3: Start Kafka
echo -e "\n${BLUE}Step 3: Starting Kafka cluster...${NC}"

docker compose up -d kafka-1 kafka-2 kafka-3 schema-registry

wait_for_port 9092 "Kafka Broker 1" 45
wait_for_port 9094 "Kafka Broker 2" 30
wait_for_port 9095 "Kafka Broker 3" 30
wait_for_service "http://localhost:8081/subjects" "Schema Registry" 30

# Step 4: Start monitoring services
echo -e "\n${BLUE}Step 4: Starting monitoring services...${NC}"

docker compose up -d prometheus grafana kafka-ui pgadmin elasticsearch kibana

echo "  Monitoring services starting in background..."
sleep 5

# Step 5: Setup Python environment
echo -e "\n${BLUE}Step 5: Setting up Python environment...${NC}"

cd backend

if [ ! -d "venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv venv
fi

echo "  Activating virtual environment..."
source venv/bin/activate

echo "  Installing Python dependencies..."
pip install -q -r requirements.txt

# Step 6: Run database migrations
echo -e "\n${BLUE}Step 6: Running database migrations...${NC}"

echo "  Running alembic migrations..."
alembic upgrade head 2>/dev/null || {
    echo -e "  ${YELLOW}Migration warning - this may be normal on first run${NC}"
}

cd "$PROJECT_ROOT"

# Step 7: Setup frontend
echo -e "\n${BLUE}Step 7: Setting up frontend...${NC}"

cd frontend/apps/prm-dashboard

if [ ! -d "node_modules" ]; then
    echo "  Installing npm dependencies..."
    npm install
else
    echo "  ✅ node_modules exists"
fi

cd "$PROJECT_ROOT"

# Final summary
echo -e "\n${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}                    Setup Complete!                              ${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"

echo -e "\n${BLUE}Infrastructure Services:${NC}"
echo "  • PostgreSQL:      localhost:5432"
echo "  • Redis:           localhost:6379"
echo "  • Kafka:           localhost:9092, 9094, 9095"
echo "  • Schema Registry: http://localhost:8081"

echo -e "\n${BLUE}Monitoring:${NC}"
echo "  • Grafana:         http://localhost:3001 (admin/admin)"
echo "  • Prometheus:      http://localhost:9090"
echo "  • Kafka UI:        http://localhost:8090"
echo "  • pgAdmin:         http://localhost:5050 (admin@healthtech.com/admin)"
echo "  • Kibana:          http://localhost:5601"

echo -e "\n${BLUE}Next Steps:${NC}"
echo -e "${YELLOW}1. Start the backend:${NC}"
echo "   cd backend && source venv/bin/activate"
echo "   uvicorn services.prm_service.main:app --host 0.0.0.0 --port 8007 --reload"

echo -e "\n${YELLOW}2. Start the frontend (in a new terminal):${NC}"
echo "   cd frontend/apps/prm-dashboard"
echo "   npm run dev"

echo -e "\n${YELLOW}3. Open the application:${NC}"
echo "   • Frontend: http://localhost:3000"
echo "   • API Docs: http://localhost:8007/docs"

echo -e "\n${YELLOW}⚠️  Don't forget to update your .env files with real API keys!${NC}"
echo ""
