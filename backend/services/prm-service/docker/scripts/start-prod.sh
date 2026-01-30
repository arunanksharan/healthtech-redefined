#!/bin/bash
# =============================================================================
# Start PRM Service - Production Mode
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

cd "$DOCKER_DIR"

echo "🚀 Starting PRM Service in Production Mode..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found!"
    echo "   Please copy .env.example to .env and configure it."
    exit 1
fi

# Validate required environment variables
source .env
if [ -z "$SECRET_KEY" ] || [ "$SECRET_KEY" = "your-secret-key-change-in-production" ]; then
    echo "❌ Error: SECRET_KEY is not set or using default value!"
    exit 1
fi

# Build and start services
echo "🔨 Building containers..."
docker compose -f docker-compose.yml build

echo "🐳 Starting services..."
docker compose -f docker-compose.yml up -d

echo ""
echo "✅ PRM Service is starting up in Production Mode!"
echo ""
echo "📍 Access Points:"
echo "   • API:          http://localhost:${APP_PORT:-8000}"
echo "   • Health:       http://localhost:${APP_PORT:-8000}/health"
echo ""
echo "📋 Commands:"
echo "   • Logs:    docker compose -f docker-compose.yml logs -f prm-service"
echo "   • Stop:    docker compose -f docker-compose.yml down"
echo "   • Monitor: docker compose -f docker-compose.yml ps"
echo ""
