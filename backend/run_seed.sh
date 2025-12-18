#!/bin/bash
#
# PRM Service Database Seeder Script
# ===================================
#
# This script automates the database seeding process for the PRM Service.
# It handles environment setup, dependency checks, and runs the Python seeder.
#
# Usage:
#   ./run_seed.sh [OPTIONS]
#
# Options:
#   -d, --database-url URL    PostgreSQL database URL
#   -f, --seed-file FILE      Path to seed data JSON file
#   -x, --drop-existing       Drop existing data before seeding (DANGEROUS!)
#   -v, --verbose             Enable verbose logging
#   -h, --help                Show this help message
#
# Environment Variables:
#   DATABASE_URL              PostgreSQL connection URL
#   VIRTUAL_ENV               Path to Python virtual environment
#
# Examples:
#   ./run_seed.sh
#   ./run_seed.sh -d "postgresql://user:pass@localhost:5432/healthtech"
#   ./run_seed.sh --drop-existing
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_DIR="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$(dirname "$(dirname "$SERVICE_DIR")")"

# Default values
DATABASE_URL="${DATABASE_URL:-postgresql://healthtech:healthtech@localhost:5432/healthtech}"
SEED_FILE="${SCRIPT_DIR}/seed_data.json"
DROP_EXISTING=""
VERBOSE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--database-url)
            DATABASE_URL="$2"
            shift 2
            ;;
        -f|--seed-file)
            SEED_FILE="$2"
            shift 2
            ;;
        -x|--drop-existing)
            DROP_EXISTING="--drop-existing"
            shift
            ;;
        -v|--verbose)
            VERBOSE="--verbose"
            shift
            ;;
        -h|--help)
            echo "PRM Service Database Seeder"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -d, --database-url URL    PostgreSQL database URL"
            echo "  -f, --seed-file FILE      Path to seed data JSON file"
            echo "  -x, --drop-existing       Drop existing data before seeding"
            echo "  -v, --verbose             Enable verbose logging"
            echo "  -h, --help                Show this help message"
            echo ""
            echo "Environment Variables:"
            echo "  DATABASE_URL              PostgreSQL connection URL"
            echo "  VIRTUAL_ENV               Path to Python virtual environment"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Print header
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}     PRM Service Database Seeder${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Check for Python
echo -e "${YELLOW}Checking Python installation...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo -e "${RED}Error: Python is not installed or not in PATH${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo -e "${GREEN}Found: $PYTHON_VERSION${NC}"

# Check/activate virtual environment
echo ""
echo -e "${YELLOW}Checking virtual environment...${NC}"

# Try to find virtual environment in common locations
VENV_PATHS=(
    "${VIRTUAL_ENV}"
    "${BACKEND_DIR}/venv"
    "${BACKEND_DIR}/.venv"
    "${SERVICE_DIR}/venv"
    "${SERVICE_DIR}/.venv"
)

VENV_FOUND=""
for venv_path in "${VENV_PATHS[@]}"; do
    if [[ -n "$venv_path" && -d "$venv_path" && -f "$venv_path/bin/activate" ]]; then
        VENV_FOUND="$venv_path"
        break
    fi
done

if [[ -n "$VENV_FOUND" ]]; then
    echo -e "${GREEN}Found virtual environment: $VENV_FOUND${NC}"
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    # shellcheck source=/dev/null
    source "$VENV_FOUND/bin/activate"
    PYTHON_CMD="python"
else
    echo -e "${YELLOW}No virtual environment found, using system Python${NC}"
fi

# Check required packages
echo ""
echo -e "${YELLOW}Checking required Python packages...${NC}"

REQUIRED_PACKAGES=("sqlalchemy" "loguru")
MISSING_PACKAGES=()

for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if ! $PYTHON_CMD -c "import $pkg" 2>/dev/null; then
        MISSING_PACKAGES+=("$pkg")
    fi
done

if [[ ${#MISSING_PACKAGES[@]} -gt 0 ]]; then
    echo -e "${YELLOW}Installing missing packages: ${MISSING_PACKAGES[*]}${NC}"
    $PYTHON_CMD -m pip install "${MISSING_PACKAGES[@]}" --quiet
fi

# Also try to install psycopg2 if not present
if ! $PYTHON_CMD -c "import psycopg2" 2>/dev/null; then
    echo -e "${YELLOW}Installing psycopg2-binary...${NC}"
    $PYTHON_CMD -m pip install psycopg2-binary --quiet 2>/dev/null || true
fi

# Try python-dotenv for .env file support
if ! $PYTHON_CMD -c "import dotenv" 2>/dev/null; then
    echo -e "${YELLOW}Installing python-dotenv...${NC}"
    $PYTHON_CMD -m pip install python-dotenv --quiet 2>/dev/null || true
fi

echo -e "${GREEN}All required packages are installed${NC}"

# Check seed file exists
echo ""
echo -e "${YELLOW}Checking seed file...${NC}"
if [[ ! -f "$SEED_FILE" ]]; then
    echo -e "${RED}Error: Seed file not found: $SEED_FILE${NC}"
    exit 1
fi
echo -e "${GREEN}Found seed file: $SEED_FILE${NC}"

# Check database connection
echo ""
echo -e "${YELLOW}Testing database connection...${NC}"

# Extract host from DATABASE_URL for display (hide password)
DB_DISPLAY=$(echo "$DATABASE_URL" | sed 's/:\/\/[^:]*:[^@]*@/:\/\/***:***@/')
echo -e "${BLUE}Database: $DB_DISPLAY${NC}"

# Test connection using Python
if ! $PYTHON_CMD -c "
from sqlalchemy import create_engine, text
try:
    engine = create_engine('$DATABASE_URL')
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('OK')
except Exception as e:
    print(f'FAILED: {e}')
    exit(1)
" 2>/dev/null; then
    echo -e "${RED}Error: Cannot connect to database${NC}"
    echo -e "${YELLOW}Please check:${NC}"
    echo -e "  1. PostgreSQL is running"
    echo -e "  2. Database exists"
    echo -e "  3. Credentials are correct"
    echo -e "  4. DATABASE_URL is set correctly"
    exit 1
fi
echo -e "${GREEN}Database connection successful!${NC}"

# Warn about drop-existing
if [[ -n "$DROP_EXISTING" ]]; then
    echo ""
    echo -e "${RED}============================================================${NC}"
    echo -e "${RED}WARNING: --drop-existing flag is set!${NC}"
    echo -e "${RED}This will DELETE ALL existing data in the database!${NC}"
    echo -e "${RED}============================================================${NC}"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " -r
    if [[ ! $REPLY == "yes" ]]; then
        echo -e "${YELLOW}Operation cancelled.${NC}"
        exit 0
    fi
fi

# Run the seeder
echo ""
echo -e "${BLUE}============================================================${NC}"
echo -e "${BLUE}     Starting Database Seeding${NC}"
echo -e "${BLUE}============================================================${NC}"
echo ""

# Build command
CMD="$PYTHON_CMD ${SCRIPT_DIR}/seed_database.py"
CMD="$CMD --database-url \"$DATABASE_URL\""
CMD="$CMD --seed-file \"$SEED_FILE\""
[[ -n "$DROP_EXISTING" ]] && CMD="$CMD $DROP_EXISTING"
[[ -n "$VERBOSE" ]] && CMD="$CMD $VERBOSE"

# Execute
eval "$CMD"
EXIT_CODE=$?

echo ""
if [[ $EXIT_CODE -eq 0 ]]; then
    echo -e "${GREEN}============================================================${NC}"
    echo -e "${GREEN}     Database Seeding Completed Successfully!${NC}"
    echo -e "${GREEN}============================================================${NC}"
else
    echo -e "${RED}============================================================${NC}"
    echo -e "${RED}     Database Seeding Failed!${NC}"
    echo -e "${RED}============================================================${NC}"
fi

exit $EXIT_CODE
