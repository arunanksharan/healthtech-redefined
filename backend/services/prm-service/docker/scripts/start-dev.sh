#!/bin/bash
# =============================================================================
# Start PRM Service - Development Mode
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

cd "$DOCKER_DIR"

echo "🚀 Starting PRM Service in Development Mode..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
fi

# Build and start services
echo "🔨 Building containers..."
docker compose -f docker-compose.dev.yml build

echo "🐳 Starting services..."
docker compose -f docker-compose.dev.yml up -d

echo ""
echo "✅ PRM Service is starting up!"
echo ""
echo "📍 Access Points:"
echo "   • API:          http://localhost:8000"
echo "   • Swagger Docs: http://localhost:8000/docs"
echo "   • ReDoc:        http://localhost:8000/redoc"
echo "   • Health:       http://localhost:8000/health"
echo "   • MinIO:        http://localhost:9001 (minioadmin/minioadmin)"
echo ""
echo "🗄️  Database: postgresql://prm:prm_dev@localhost:5433/prm_dev"
echo "💾 Redis:    redis://localhost:6379"
echo ""
echo "📋 Commands:"
echo "   • Logs:  docker compose -f docker-compose.dev.yml logs -f prm-service"
echo "   • Stop:  docker compose -f docker-compose.dev.yml down"
echo "   • Tools: docker compose -f docker-compose.dev.yml --profile tools up -d"
echo ""
