#!/bin/bash
# =============================================================================
# Run PRM Service Tests
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$(dirname "$SCRIPT_DIR")"

cd "$DOCKER_DIR"

echo "🧪 Running PRM Service Tests..."

# Build test container
echo "🔨 Building test container..."
docker compose -f docker-compose.test.yml build

# Run tests
echo "🚀 Running tests..."
docker compose -f docker-compose.test.yml up \
    --abort-on-container-exit \
    --exit-code-from prm-test

EXIT_CODE=$?

# Copy test results to host
echo "📋 Copying test results..."
docker cp prm-test-runner:/app/test-results ./test-results 2>/dev/null || true
docker cp prm-test-runner:/app/coverage ./coverage 2>/dev/null || true

# Cleanup
echo "🧹 Cleaning up..."
docker compose -f docker-compose.test.yml down -v

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ All tests passed!"
    echo ""
    echo "📊 Results available in:"
    echo "   • ./test-results/junit.xml"
    echo "   • ./coverage/index.html"
else
    echo ""
    echo "❌ Tests failed with exit code: $EXIT_CODE"
fi

exit $EXIT_CODE
