# PRM Dashboard - Docker Makefile
# Easy commands for Docker operations

.PHONY: help build up down logs shell clean dev full monitoring

# Default target
help:
	@echo "PRM Dashboard - Docker Commands"
	@echo "================================"
	@echo ""
	@echo "Quick Start:"
	@echo "  make setup        - Copy .env.docker to .env (first time setup)"
	@echo "  make dev          - Start development mode with hot-reload"
	@echo "  make up           - Start frontend only (standalone)"
	@echo "  make full         - Start full stack (frontend + backend + db)"
	@echo ""
	@echo "Commands:"
	@echo "  make build        - Build Docker images"
	@echo "  make up           - Start containers (standalone frontend)"
	@echo "  make down         - Stop all containers"
	@echo "  make logs         - View container logs"
	@echo "  make shell        - Open shell in frontend container"
	@echo "  make clean        - Remove containers, images, and volumes"
	@echo ""
	@echo "Full Stack:"
	@echo "  make full         - Start full stack"
	@echo "  make full-down    - Stop full stack"
	@echo "  make full-logs    - View full stack logs"
	@echo ""
	@echo "Development:"
	@echo "  make dev          - Start in development mode"
	@echo "  make dev-down     - Stop development mode"
	@echo ""
	@echo "Optional Profiles:"
	@echo "  make full-nginx   - Full stack with Nginx reverse proxy"
	@echo "  make monitoring   - Full stack with Prometheus + Grafana"
	@echo ""

# =============================================================================
# Setup
# =============================================================================

setup:
	@if [ ! -f .env ]; then \
		cp .env.docker .env; \
		echo "Created .env from .env.docker"; \
		echo "Please edit .env with your configuration"; \
	else \
		echo ".env already exists. Skipping."; \
	fi

# =============================================================================
# Standalone Frontend
# =============================================================================

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

shell:
	docker compose exec prm-dashboard sh

restart:
	docker compose restart prm-dashboard

# =============================================================================
# Development Mode
# =============================================================================

dev:
	docker compose -f docker-compose.dev.yml up -d

dev-build:
	docker compose -f docker-compose.dev.yml build

dev-down:
	docker compose -f docker-compose.dev.yml down

dev-logs:
	docker compose -f docker-compose.dev.yml logs -f

dev-shell:
	docker compose -f docker-compose.dev.yml exec prm-dashboard-dev sh

# =============================================================================
# Full Stack
# =============================================================================

full:
	docker compose -f docker-compose.full.yml up -d

full-build:
	docker compose -f docker-compose.full.yml build

full-down:
	docker compose -f docker-compose.full.yml down

full-logs:
	docker compose -f docker-compose.full.yml logs -f

full-shell-frontend:
	docker compose -f docker-compose.full.yml exec prm-dashboard sh

full-shell-backend:
	docker compose -f docker-compose.full.yml exec prm-service bash

full-shell-db:
	docker compose -f docker-compose.full.yml exec postgres psql -U postgres -d prm_db

# =============================================================================
# Optional Profiles
# =============================================================================

# Full stack with Nginx reverse proxy
full-nginx:
	docker compose -f docker-compose.full.yml --profile with-nginx up -d

# Full stack with monitoring (Prometheus + Grafana)
monitoring:
	docker compose -f docker-compose.full.yml --profile with-monitoring up -d

# All services including Nginx and monitoring
full-all:
	docker compose -f docker-compose.full.yml --profile with-nginx --profile with-monitoring up -d

# =============================================================================
# Cleanup
# =============================================================================

clean:
	docker compose down -v --rmi local
	docker compose -f docker-compose.dev.yml down -v --rmi local 2>/dev/null || true
	docker compose -f docker-compose.full.yml down -v --rmi local 2>/dev/null || true

clean-all:
	docker compose down -v --rmi all
	docker compose -f docker-compose.dev.yml down -v --rmi all 2>/dev/null || true
	docker compose -f docker-compose.full.yml down -v --rmi all 2>/dev/null || true
	docker system prune -f

# =============================================================================
# Database Management
# =============================================================================

db-migrate:
	docker compose -f docker-compose.full.yml exec prm-service alembic upgrade head

db-rollback:
	docker compose -f docker-compose.full.yml exec prm-service alembic downgrade -1

db-shell:
	docker compose -f docker-compose.full.yml exec postgres psql -U postgres -d prm_db

# =============================================================================
# Health Checks
# =============================================================================

health:
	@echo "Checking service health..."
	@curl -s http://localhost:3000/ > /dev/null && echo "Frontend: ✓ Running" || echo "Frontend: ✗ Not running"
	@curl -s http://localhost:8000/health > /dev/null && echo "Backend:  ✓ Running" || echo "Backend:  ✗ Not running"
	@docker compose exec redis redis-cli ping > /dev/null 2>&1 && echo "Redis:    ✓ Running" || echo "Redis:    ✗ Not running"
	@docker compose exec postgres pg_isready > /dev/null 2>&1 && echo "Postgres: ✓ Running" || echo "Postgres: ✗ Not running"

# =============================================================================
# Utility
# =============================================================================

ps:
	docker compose ps
	@echo ""
	docker compose -f docker-compose.full.yml ps 2>/dev/null || true

images:
	docker images | grep prm

prune:
	docker system prune -f
	docker volume prune -f
