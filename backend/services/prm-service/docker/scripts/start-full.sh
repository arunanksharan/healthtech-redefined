#!/bin/bash
# =============================================================================
# Start PRM Service - Full Stack (with Kafka, Monitoring, Storage)
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

cd "$DOCKER_DIR"

echo "🚀 Starting PRM Service - Full Stack..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
fi

# Build and start services
echo "🔨 Building containers..."
docker compose -f docker-compose.full.yml build

echo "🐳 Starting full stack services..."
docker compose -f docker-compose.full.yml up -d

echo ""
echo "✅ PRM Service Full Stack is starting up!"
echo ""
echo "📍 Access Points:"
echo "   • API:          http://localhost:${APP_PORT:-8000}"
echo "   • Swagger Docs: http://localhost:${APP_PORT:-8000}/docs"
echo "   • Health:       http://localhost:${APP_PORT:-8000}/health"
echo ""
echo "🗄️  Infrastructure:"
echo "   • PostgreSQL:   localhost:5433"
echo "   • Redis:        localhost:6379"
echo "   • Kafka:        localhost:9092"
echo "   • MinIO:        http://localhost:9001 (minioadmin/minioadmin)"
echo ""
echo "📊 Monitoring:"
echo "   • Prometheus:   http://localhost:9090"
echo "   • Grafana:      http://localhost:3002 (admin/admin)"
echo ""
echo "📋 Commands:"
echo "   • Logs:  docker compose -f docker-compose.full.yml logs -f prm-service"
echo "   • Stop:  docker compose -f docker-compose.full.yml down"
echo "   • Proxy: docker compose -f docker-compose.full.yml --profile with-proxy up -d"
echo ""
