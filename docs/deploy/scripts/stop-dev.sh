#!/bin/bash
#
# HealthTech Platform - Development Stop Script
#
# This script stops all infrastructure services.
# Usage: ./docs/deploy/scripts/stop-dev.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           HealthTech PRM Platform - Stop Services              ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
cd "$PROJECT_ROOT"

# Parse arguments
REMOVE_VOLUMES=false
if [ "$1" == "--clean" ] || [ "$1" == "-c" ]; then
    REMOVE_VOLUMES=true
fi

echo -e "${YELLOW}Stopping all services...${NC}"

if [ "$REMOVE_VOLUMES" = true ]; then
    echo -e "${RED}⚠️  Also removing volumes (data will be lost)${NC}"
    docker compose down --volumes --remove-orphans
else
    docker compose down --remove-orphans
fi

echo -e "\n${GREEN}All services stopped.${NC}"

if [ "$REMOVE_VOLUMES" = false ]; then
    echo -e "\n${BLUE}Data volumes preserved. To remove all data, run:${NC}"
    echo "  ./docs/deploy/scripts/stop-dev.sh --clean"
fi

echo ""
