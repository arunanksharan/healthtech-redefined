#!/bin/bash
# ============================================================================
# HealthTech Backend - Stop All Services
# ============================================================================

echo "Stopping all HealthTech backend services..."
pm2 stop all
pm2 delete all
echo "All services stopped."
pm2 list
