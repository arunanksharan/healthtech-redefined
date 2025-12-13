# HealthTech PRM Platform - Complete Deployment Guide

> Step-by-step instructions to deploy the entire HealthTech Patient Relationship Management platform

## Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Architecture Overview](#2-architecture-overview)
3. [Quick Start (Development)](#3-quick-start-development)
4. [Detailed Setup](#4-detailed-setup)
5. [Service Startup Order](#5-service-startup-order)
6. [Health Verification](#6-health-verification)
7. [Production Deployment](#7-production-deployment)
8. [Monitoring Setup](#8-monitoring-setup)

---

## 1. Prerequisites

### Required Software

| Software | Version | Check Command | Installation |
|----------|---------|---------------|--------------|
| Docker | 24.0+ | `docker --version` | [docs.docker.com](https://docs.docker.com/get-docker/) |
| Docker Compose | 2.20+ | `docker compose version` | Included with Docker Desktop |
| Python | 3.11+ | `python3 --version` | [python.org](https://www.python.org/downloads/) |
| Node.js | 18+ | `node --version` | [nodejs.org](https://nodejs.org/) |
| npm | 9+ | `npm --version` | Included with Node.js |
| Git | 2.40+ | `git --version` | [git-scm.com](https://git-scm.com/) |

### System Requirements

| Environment | CPU | RAM | Storage |
|-------------|-----|-----|---------|
| Development | 4 cores | 16 GB | 50 GB SSD |
| Staging | 8 cores | 32 GB | 100 GB SSD |
| Production | 16+ cores | 64+ GB | 500+ GB SSD |

### External Services (Required)

You will need accounts and API keys for:

| Service | Purpose | Sign Up |
|---------|---------|---------|
| OpenAI | AI/LLM features | [platform.openai.com](https://platform.openai.com/) |
| LiveKit | Voice/Video calls | [livekit.io](https://livekit.io/) |
| Twilio | SMS/WhatsApp | [twilio.com](https://www.twilio.com/) |
| AWS S3 | File storage | [aws.amazon.com](https://aws.amazon.com/) |
| Sentry | Error tracking | [sentry.io](https://sentry.io/) (optional) |

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              CLIENTS                                      │
│         Browser (3000)    │    Mobile App    │    WhatsApp/Voice         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND LAYER                                    │
│                                                                           │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐         │
│   │  PRM Dashboard  │  │  Patient Portal │  │  Doctor Portal  │         │
│   │   (Port 3000)   │  │   (Port 3002)   │  │   (Port 3003)   │         │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY / LOAD BALANCER                       │
│                              (Port 80/443)                                │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         BACKEND SERVICES                                  │
│                                                                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐            │
│  │   Auth     │ │  Identity  │ │   FHIR     │ │  Consent   │            │
│  │   8004     │ │   8001     │ │   8002     │ │   8003     │            │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘            │
│                                                                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐            │
│  │ Scheduling │ │ Encounter  │ │    PRM     │ │   Scribe   │            │
│  │   8005     │ │   8006     │ │   8007     │ │   8008     │            │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘            │
│                                                                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐            │
│  │    Bed     │ │ Admission  │ │  Nursing   │ │   Orders   │            │
│  │   8009     │ │   8010     │ │   8011     │ │   8012     │            │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘            │
│                                                                           │
│           + 48 additional specialized microservices                       │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                        │
│                                                                           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────────────┐ │
│  │   PostgreSQL   │  │     Redis      │  │         Kafka              │ │
│  │    (5432)      │  │    (6379)      │  │   (9092, 9094, 9095)       │ │
│  └────────────────┘  └────────────────┘  └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         MONITORING                                        │
│                                                                           │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐             │
│  │   Prometheus   │  │    Grafana     │  │ Elasticsearch  │             │
│  │    (9090)      │  │    (3001)      │  │    (9200)      │             │
│  └────────────────┘  └────────────────┘  └────────────────┘             │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Quick Start (Development)

For a quick development setup, run the following:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/healthtech-redefined.git
cd healthtech-redefined

# 2. Copy environment templates
cp docs/deploy/env-templates/.env.backend.example backend/.env
cp docs/deploy/env-templates/.env.frontend.example frontend/apps/prm-dashboard/.env.local

# 3. Start infrastructure (PostgreSQL, Redis, Kafka)
docker compose up -d postgres redis zookeeper kafka-1 kafka-2 kafka-3

# 4. Wait for services to be healthy (30 seconds)
sleep 30

# 5. Run database migrations
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
cd ..

# 6. Start backend services (in new terminal)
cd backend
source venv/bin/activate
uvicorn services.prm_service.main:app --host 0.0.0.0 --port 8007 --reload

# 7. Start frontend (in new terminal)
cd frontend/apps/prm-dashboard
npm install
npm run dev

# 8. Open browser
# Frontend: http://localhost:3000
# API Docs: http://localhost:8007/docs
```

---

## 4. Detailed Setup

### Step 4.1: Clone and Initialize

```bash
# Clone repository
git clone https://github.com/your-org/healthtech-redefined.git
cd healthtech-redefined

# Verify structure
ls -la
# Should see: backend/, frontend/, docs/, infrastructure/, docker-compose.yml
```

### Step 4.2: Environment Configuration

#### Backend Environment (`backend/.env`)

```bash
# Copy template
cp docs/deploy/env-templates/.env.backend.example backend/.env

# Edit with your values
nano backend/.env  # or use your preferred editor
```

**Required variables to configure:**

```bash
# Database (change password for production)
DATABASE_URL=postgresql://healthtech:healthtech@localhost:5432/healthtech

# Security (MUST change in production)
JWT_SECRET_KEY=your-secret-key-min-32-characters-long-change-me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://localhost:6379/0

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_ENABLED=true

# OpenAI (required for AI features)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Environment
ENVIRONMENT=development
DEBUG=true
```

#### Frontend Environment (`frontend/apps/prm-dashboard/.env.local`)

```bash
# Copy template
cp docs/deploy/env-templates/.env.frontend.example frontend/apps/prm-dashboard/.env.local

# Edit with your values
nano frontend/apps/prm-dashboard/.env.local
```

**Required variables:**

```bash
# API Connection
NEXT_PUBLIC_API_URL=http://localhost:8007
NEXT_PUBLIC_WS_URL=ws://localhost:8007

# OpenAI (for client-side AI features)
OPENAI_API_KEY=sk-your-openai-api-key-here

# LiveKit (for telehealth video calls)
NEXT_PUBLIC_LIVEKIT_URL=wss://your-livekit.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret

# Feature Flags
NEXT_PUBLIC_ENABLE_VOICE=true
NEXT_PUBLIC_ENABLE_AI_ASSISTANT=true
```

### Step 4.3: Start Infrastructure Services

```bash
# Start all infrastructure services
docker compose up -d

# Verify services are running
docker compose ps

# Expected output:
# NAME                STATUS              PORTS
# postgres            running (healthy)   0.0.0.0:5432->5432/tcp
# redis               running             0.0.0.0:6379->6379/tcp
# zookeeper           running             0.0.0.0:2181->2181/tcp
# kafka-1             running             0.0.0.0:9092->9092/tcp
# kafka-2             running             0.0.0.0:9094->9094/tcp
# kafka-3             running             0.0.0.0:9095->9095/tcp
# schema-registry     running             0.0.0.0:8081->8081/tcp
# kafka-ui            running             0.0.0.0:8090->8090/tcp
# prometheus          running             0.0.0.0:9090->9090/tcp
# grafana             running             0.0.0.0:3001->3001/tcp
# elasticsearch       running             0.0.0.0:9200->9200/tcp
# kibana              running             0.0.0.0:5601->5601/tcp
# pgadmin             running             0.0.0.0:5050->5050/tcp
```

### Step 4.4: Database Setup

```bash
# Enter backend directory
cd backend

# Create Python virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate    # Windows

# Install dependencies
pip install -r requirements.txt

# Verify database connection
python -c "from sqlalchemy import create_engine; e = create_engine('postgresql://healthtech:healthtech@localhost:5432/healthtech'); e.connect(); print('Database connected!')"

# Run all migrations
alembic upgrade head

# Verify migrations
alembic current
# Should show latest migration version
```

### Step 4.5: Start Backend Services

You have two options:

#### Option A: Start Core Services Only (Recommended for Development)

```bash
# Terminal 1: PRM Service (main service)
cd backend
source venv/bin/activate
uvicorn services.prm_service.main:app --host 0.0.0.0 --port 8007 --reload

# Terminal 2: Auth Service
uvicorn services.auth_service.main:app --host 0.0.0.0 --port 8004 --reload

# Terminal 3: FHIR Service
uvicorn services.fhir_service.main:app --host 0.0.0.0 --port 8002 --reload
```

#### Option B: Start All Services via Docker

```bash
# Build and start all backend services
cd backend
docker compose -f docker-compose.services.yml up -d
```

### Step 4.6: Start Frontend

```bash
# Enter frontend directory
cd frontend/apps/prm-dashboard

# Install dependencies
npm install

# Start development server
npm run dev

# Frontend will be available at http://localhost:3000
```

---

## 5. Service Startup Order

Services must be started in this specific order due to dependencies:

```
Phase 1: Infrastructure (no dependencies)
├── PostgreSQL (5432)
├── Redis (6379)
└── Zookeeper (2181)

Phase 2: Message Queue (depends on Zookeeper)
├── Kafka Broker 1 (9092)
├── Kafka Broker 2 (9094)
├── Kafka Broker 3 (9095)
└── Schema Registry (8081)

Phase 3: Core Backend (depends on PostgreSQL, Redis, Kafka)
├── Auth Service (8004)         # First - handles authentication
├── Identity Service (8001)     # User management
├── Consent Service (8003)      # Patient consent
└── FHIR Service (8002)         # Clinical data

Phase 4: Business Logic (depends on Core Backend)
├── PRM Service (8007)          # Main business logic
├── Scheduling Service (8005)   # Appointments
├── Encounter Service (8006)    # Clinical encounters
└── Scribe Service (8008)       # AI documentation

Phase 5: Extended Services (depends on Business Logic)
├── Orders Service (8012)
├── Nursing Service (8011)
├── Admission Service (8010)
├── Bed Management (8009)
└── ICU Service (8013)

Phase 6: Frontend (depends on Backend APIs)
└── PRM Dashboard (3000)

Phase 7: Monitoring (can start anytime)
├── Prometheus (9090)
├── Grafana (3001)
├── Elasticsearch (9200)
├── Kibana (5601)
└── Kafka UI (8090)
```

### Automated Startup Script

Save this as `start-dev.sh`:

```bash
#!/bin/bash
set -e

echo "=== Starting HealthTech Platform ==="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1

    echo -n "Waiting for $name..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s "$url" > /dev/null 2>&1; then
            echo -e "${GREEN} Ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo -e "${RED} Failed!${NC}"
    return 1
}

# Phase 1: Infrastructure
echo ""
echo "=== Phase 1: Starting Infrastructure ==="
docker compose up -d postgres redis zookeeper
sleep 5

wait_for_service "http://localhost:5432" "PostgreSQL" || true
wait_for_service "http://localhost:6379" "Redis" || true

# Phase 2: Kafka
echo ""
echo "=== Phase 2: Starting Kafka ==="
docker compose up -d kafka-1 kafka-2 kafka-3 schema-registry
sleep 10

wait_for_service "http://localhost:8081" "Schema Registry"

# Phase 3: Run migrations
echo ""
echo "=== Phase 3: Running Database Migrations ==="
cd backend
source venv/bin/activate
alembic upgrade head
cd ..

# Phase 4: Monitoring (optional)
echo ""
echo "=== Phase 4: Starting Monitoring ==="
docker compose up -d prometheus grafana kafka-ui pgadmin

echo ""
echo -e "${GREEN}=== Infrastructure Ready ===${NC}"
echo ""
echo "To start backend services:"
echo "  cd backend && source venv/bin/activate"
echo "  uvicorn services.prm_service.main:app --port 8007 --reload"
echo ""
echo "To start frontend:"
echo "  cd frontend/apps/prm-dashboard && npm run dev"
echo ""
echo "Access points:"
echo "  - Frontend:      http://localhost:3000"
echo "  - API Docs:      http://localhost:8007/docs"
echo "  - Kafka UI:      http://localhost:8090"
echo "  - Grafana:       http://localhost:3001 (admin/admin)"
echo "  - pgAdmin:       http://localhost:5050 (admin@healthtech.com/admin)"
```

---

## 6. Health Verification

### Check All Services

```bash
# Infrastructure
curl http://localhost:5432 2>&1 | grep -q "invalid" && echo "PostgreSQL: OK" || echo "PostgreSQL: DOWN"
curl -s http://localhost:6379/ping | grep -q "PONG" || redis-cli ping | grep -q "PONG" && echo "Redis: OK" || echo "Redis: DOWN"
curl -s http://localhost:8081/subjects && echo "Schema Registry: OK" || echo "Schema Registry: DOWN"

# Backend Services
curl -s http://localhost:8004/health | jq .status
curl -s http://localhost:8007/health | jq .status
curl -s http://localhost:8002/health | jq .status

# Frontend
curl -s http://localhost:3000 > /dev/null && echo "Frontend: OK" || echo "Frontend: DOWN"

# Monitoring
curl -s http://localhost:9090/-/healthy && echo "Prometheus: OK"
curl -s http://localhost:3001/api/health && echo "Grafana: OK"
```

### Health Check Script

Save as `health-check.sh`:

```bash
#!/bin/bash

echo "=== HealthTech Platform Health Check ==="
echo ""

check_service() {
    local name=$1
    local url=$2
    local expected=$3

    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    if [ "$response" = "$expected" ]; then
        echo "✅ $name: Healthy"
    else
        echo "❌ $name: Unhealthy (HTTP $response)"
    fi
}

echo "Infrastructure:"
check_service "PostgreSQL" "http://localhost:5432" "000"  # Postgres doesn't respond to HTTP
docker compose ps postgres | grep -q "healthy" && echo "✅ PostgreSQL: Healthy" || echo "❌ PostgreSQL: Unhealthy"
check_service "Redis" "http://localhost:6379" "000"
docker compose ps redis | grep -q "running" && echo "✅ Redis: Running" || echo "❌ Redis: Down"
check_service "Schema Registry" "http://localhost:8081/subjects" "200"

echo ""
echo "Backend Services:"
check_service "Auth Service" "http://localhost:8004/health" "200"
check_service "Identity Service" "http://localhost:8001/health" "200"
check_service "FHIR Service" "http://localhost:8002/health" "200"
check_service "PRM Service" "http://localhost:8007/health" "200"

echo ""
echo "Frontend:"
check_service "PRM Dashboard" "http://localhost:3000" "200"

echo ""
echo "Monitoring:"
check_service "Prometheus" "http://localhost:9090/-/healthy" "200"
check_service "Grafana" "http://localhost:3001/api/health" "200"
check_service "Kafka UI" "http://localhost:8090" "200"
```

---

## 7. Production Deployment

### Step 7.1: Security Hardening

```bash
# Generate strong secrets
openssl rand -base64 32  # For JWT_SECRET_KEY
openssl rand -base64 24  # For database passwords

# Update production environment files
# NEVER use default passwords in production!
```

### Step 7.2: Production Environment Variables

Create `backend/.env.production`:

```bash
# Database - Use strong password, consider connection pooling
DATABASE_URL=postgresql://prm_prod:STRONG_PASSWORD_HERE@db-host:5432/healthtech_prod

# Security - Generate with: openssl rand -base64 32
JWT_SECRET_KEY=GENERATED_SECRET_KEY_HERE
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis - Use password in production
REDIS_URL=redis://:REDIS_PASSWORD@redis-host:6379/0

# Kafka - Use SSL in production
KAFKA_BOOTSTRAP_SERVERS=kafka-1:9092,kafka-2:9092,kafka-3:9092
KAFKA_ENABLED=true
KAFKA_SECURITY_PROTOCOL=SASL_SSL

# AI Services
OPENAI_API_KEY=sk-prod-key-here
ANTHROPIC_API_KEY=sk-ant-prod-key-here

# External Services
TWILIO_ACCOUNT_SID=ACxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxx
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx

# AWS
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET_NAME=healthtech-prod-bucket

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/xxx

# Environment
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# HIPAA Compliance
HIPAA_MODE=true
AUDIT_LOG_RETENTION_DAYS=2190
PHI_ENCRYPTION_ENABLED=true
```

### Step 7.3: Docker Production Build

```bash
# Build production images
docker build -t healthtech/prm-service:latest -f backend/services/prm-service/Dockerfile backend/
docker build -t healthtech/prm-dashboard:latest -f frontend/apps/prm-dashboard/Dockerfile frontend/apps/prm-dashboard/

# Tag for registry
docker tag healthtech/prm-service:latest your-registry.com/healthtech/prm-service:v1.0.0
docker tag healthtech/prm-dashboard:latest your-registry.com/healthtech/prm-dashboard:v1.0.0

# Push to registry
docker push your-registry.com/healthtech/prm-service:v1.0.0
docker push your-registry.com/healthtech/prm-dashboard:v1.0.0
```

### Step 7.4: Production Docker Compose

See `docs/deploy/docker/docker-compose.production.yml` for full production configuration.

---

## 8. Monitoring Setup

### Grafana Dashboards

1. Access Grafana at http://localhost:3001
2. Default login: `admin` / `admin`
3. Add Prometheus data source:
   - URL: `http://prometheus:9090`
   - Access: `Server`

### Key Metrics to Monitor

| Metric | Alert Threshold | Description |
|--------|-----------------|-------------|
| API Response Time | > 500ms | Endpoint latency |
| Error Rate | > 1% | HTTP 5xx errors |
| Database Connections | > 80% | Connection pool usage |
| Memory Usage | > 85% | Container memory |
| Kafka Consumer Lag | > 1000 | Message processing delay |
| Redis Memory | > 80% | Cache memory usage |

### Log Aggregation

```bash
# View service logs
docker compose logs -f prm-service

# View all logs
docker compose logs -f

# Access Kibana for log search
open http://localhost:5601
```

---

## Next Steps

1. **Review Security**: See `docs/deploy/SECURITY-CHECKLIST.md`
2. **Configure Monitoring**: See `docs/deploy/MONITORING-SETUP.md`
3. **Troubleshooting**: See `docs/deploy/TROUBLESHOOTING.md`
4. **Port Reference**: See `docs/deploy/PORT-REFERENCE.md`

---

## Support

For issues:
1. Check `docs/deploy/TROUBLESHOOTING.md`
2. Review service logs: `docker compose logs <service-name>`
3. Open an issue on GitHub
