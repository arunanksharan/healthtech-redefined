#!/bin/bash
# ============================================================================
# HealthTech Backend - Stop All Services
# ============================================================================

echo "Stopping all HealthTech backend services..."

# Check if any PM2 processes exist before trying to stop
if pm2 list 2>/dev/null | grep -q "prm-"; then
    pm2 stop all 2>/dev/null || true
    pm2 delete all 2>/dev/null || true
    echo "All services stopped."
else
    echo "No services running."
fi

pm2 list 2>/dev/null || echo "PM2 process list is empty."
