#!/bin/bash
# ============================================================================
# HealthTech Backend - Ubuntu Server Setup Script
# ============================================================================
# This script sets up the backend on a fresh Ubuntu server (22.04 LTS+)
# Run with: sudo ./setup-ubuntu.sh
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================================================
# Configuration
# ============================================================================
APP_USER=${APP_USER:-deploy}
APP_ROOT=${APP_ROOT:-/var/www/healthtech-backend}
PYTHON_VERSION=${PYTHON_VERSION:-3.11}
NODE_VERSION=${NODE_VERSION:-20}

# ============================================================================
# Check if running as root
# ============================================================================
if [[ $EUID -ne 0 ]]; then
   echo_error "This script must be run as root (use sudo)"
   exit 1
fi

# ============================================================================
# Update system packages
# ============================================================================
echo_info "Updating system packages..."
apt-get update && apt-get upgrade -y

# ============================================================================
# Install essential packages
# ============================================================================
echo_info "Installing essential packages..."
apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    vim \
    htop \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    libpq-dev \
    libffi-dev \
    libssl-dev

# ============================================================================
# Install Python
# ============================================================================
echo_info "Installing Python ${PYTHON_VERSION}..."
add-apt-repository -y ppa:deadsnakes/ppa
apt-get update
apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python${PYTHON_VERSION}-dev \
    python${PYTHON_VERSION}-distutils \
    python3-pip

# Set Python 3.11 as default python3
update-alternatives --install /usr/bin/python3 python3 /usr/bin/python${PYTHON_VERSION} 1

# ============================================================================
# Install Node.js (for PM2)
# ============================================================================
echo_info "Installing Node.js ${NODE_VERSION}..."
curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash -
apt-get install -y nodejs

# ============================================================================
# Install PM2 globally
# ============================================================================
echo_info "Installing PM2..."
npm install -g pm2
# Note: pm2 startup will be configured after user creation

# ============================================================================
# Install PostgreSQL
# ============================================================================
echo_info "Installing PostgreSQL..."
apt-get install -y postgresql postgresql-contrib

# Start and enable PostgreSQL
systemctl start postgresql
systemctl enable postgresql

# ============================================================================
# Install Redis
# ============================================================================
echo_info "Installing Redis..."
apt-get install -y redis-server

# Configure Redis for production
sed -i 's/supervised no/supervised systemd/' /etc/redis/redis.conf

# Start and enable Redis
systemctl restart redis
systemctl enable redis

# ============================================================================
# Install Nginx (reverse proxy)
# ============================================================================
echo_info "Installing Nginx..."
apt-get install -y nginx

# Enable Nginx
systemctl enable nginx

# ============================================================================
# Create application user (if not exists)
# ============================================================================
echo_info "Setting up application user..."
if ! id "${APP_USER}" &>/dev/null; then
    useradd -m -s /bin/bash ${APP_USER}
    echo_info "Created user: ${APP_USER}"
else
    echo_info "User ${APP_USER} already exists"
fi

# Configure PM2 startup for the application user
echo_info "Configuring PM2 startup..."
pm2 startup systemd -u ${APP_USER} --hp /home/${APP_USER}

# ============================================================================
# Create application directory
# ============================================================================
echo_info "Creating application directory..."
mkdir -p ${APP_ROOT}
chown -R ${APP_USER}:${APP_USER} ${APP_ROOT}

# Create logs directory
mkdir -p ${APP_ROOT}/backend/logs
chown -R ${APP_USER}:${APP_USER} ${APP_ROOT}/backend/logs

# ============================================================================
# Create PostgreSQL database and user
# ============================================================================
echo_info "Setting up PostgreSQL database..."
sudo -u postgres psql << EOF
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'healthtech') THEN
        CREATE USER healthtech WITH PASSWORD 'healthtech';
    END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE healthtech OWNER healthtech'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'healthtech')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE healthtech TO healthtech;
EOF

echo_info "PostgreSQL database 'healthtech' created with user 'healthtech'"

# ============================================================================
# Configure firewall (UFW)
# ============================================================================
echo_info "Configuring firewall..."
ufw allow ssh
ufw allow 'Nginx Full'
ufw allow 8000:8100/tcp  # Backend service ports
ufw --force enable

# ============================================================================
# Print summary
# ============================================================================
echo ""
echo "============================================================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "============================================================================"
echo ""
echo "Installed:"
echo "  - Python ${PYTHON_VERSION}"
echo "  - Node.js ${NODE_VERSION}"
echo "  - PM2"
echo "  - PostgreSQL"
echo "  - Redis"
echo "  - Nginx"
echo ""
echo "Application:"
echo "  - User: ${APP_USER}"
echo "  - Root: ${APP_ROOT}"
echo ""
echo "Next steps:"
echo "  1. Clone your repository to ${APP_ROOT}"
echo "  2. Copy .env.example to .env and configure"
echo "  3. Run: ./scripts/deploy.sh"
echo ""
echo "Database:"
echo "  - Database: healthtech"
echo "  - User: healthtech"
echo "  - Password: healthtech (CHANGE THIS IN PRODUCTION!)"
echo ""
echo "============================================================================"
