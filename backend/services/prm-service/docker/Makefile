# =============================================================================
# PRM Service - Docker Makefile
# =============================================================================

.PHONY: help dev prod full test clean logs shell db-shell redis-shell webhooks tools stop

# Default target
help:
	@echo ""
	@echo "PRM Service - Docker Commands"
	@echo "=============================="
	@echo ""
	@echo "Development:"
	@echo "  make dev        - Start development environment (hot reload)"
	@echo "  make tools      - Start dev + admin tools (pgAdmin, Redis Commander)"
	@echo "  make webhooks   - Start dev + ngrok tunnel for Zoice webhooks"
	@echo ""
	@echo "Production:"
	@echo "  make prod       - Start production environment"
	@echo "  make full       - Start full stack (+ Kafka, monitoring)"
	@echo ""
	@echo "Testing:"
	@echo "  make test       - Run all tests in isolated environment"
	@echo ""
	@echo "Utilities:"
	@echo "  make logs       - Follow service logs"
	@echo "  make shell      - Open shell in app container"
	@echo "  make db-shell   - Open PostgreSQL shell"
	@echo "  make redis-shell - Open Redis CLI"
	@echo "  make stop       - Stop all services"
	@echo "  make clean      - Stop and remove all containers/volumes"
	@echo ""

# Development environment
dev:
	@./scripts/start-dev.sh

# Development with tools
tools:
	@docker compose -f docker-compose.dev.yml --profile tools up -d
	@echo ""
	@echo "🛠️  Admin Tools:"
	@echo "   • pgAdmin:         http://localhost:5050 (admin@prm.local / admin)"
	@echo "   • Redis Commander: http://localhost:8081"
	@echo "   • MailHog:         http://localhost:8025"
	@echo ""

# Development with webhook tunnel
webhooks:
	@./scripts/setup-webhooks.sh

# Production environment
prod:
	@./scripts/start-prod.sh

# Full stack (with Kafka, monitoring)
full:
	@./scripts/start-full.sh

# Run tests
test:
	@./scripts/run-tests.sh

# View logs
logs:
	@docker compose -f docker-compose.dev.yml logs -f prm-service

# Shell into app container
shell:
	@docker exec -it prm-service-dev /bin/bash

# PostgreSQL shell
db-shell:
	@docker exec -it prm-postgres-dev psql -U prm -d prm_dev

# Redis CLI
redis-shell:
	@docker exec -it prm-redis-dev redis-cli

# Stop all services
stop:
	@docker compose -f docker-compose.dev.yml down 2>/dev/null || true
	@docker compose -f docker-compose.yml down 2>/dev/null || true
	@docker compose -f docker-compose.full.yml down 2>/dev/null || true
	@docker compose -f docker-compose.test.yml down 2>/dev/null || true
	@echo "✅ All services stopped"

# Clean everything
clean: stop
	@docker compose -f docker-compose.dev.yml down -v --remove-orphans 2>/dev/null || true
	@docker compose -f docker-compose.yml down -v --remove-orphans 2>/dev/null || true
	@docker compose -f docker-compose.full.yml down -v --remove-orphans 2>/dev/null || true
	@docker compose -f docker-compose.test.yml down -v --remove-orphans 2>/dev/null || true
	@echo "✅ All containers and volumes removed"
