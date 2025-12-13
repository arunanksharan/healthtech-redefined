# HealthTech Platform - Troubleshooting Guide

> Solutions to common deployment and runtime issues

## Table of Contents
1. [Quick Diagnostics](#1-quick-diagnostics)
2. [Database Issues](#2-database-issues)
3. [Service Startup Issues](#3-service-startup-issues)
4. [Port Conflicts](#4-port-conflicts)
5. [Network Issues](#5-network-issues)
6. [Performance Issues](#6-performance-issues)
7. [Authentication Issues](#7-authentication-issues)
8. [Kafka Issues](#8-kafka-issues)
9. [Frontend Issues](#9-frontend-issues)
10. [Docker Issues](#10-docker-issues)

---

## 1. Quick Diagnostics

### Run Full Health Check

```bash
#!/bin/bash
# Save as health-check.sh

echo "=== HealthTech Quick Diagnostics ==="
echo ""

# Check Docker
echo "Docker Status:"
docker info > /dev/null 2>&1 && echo "✅ Docker is running" || echo "❌ Docker is not running"

# Check containers
echo ""
echo "Container Status:"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No compose project running"

# Check ports
echo ""
echo "Port Availability:"
for port in 3000 5432 6379 8007 9092; do
    lsof -i :$port > /dev/null 2>&1 && echo "⚠️  Port $port: IN USE" || echo "✅ Port $port: Available"
done

# Check services
echo ""
echo "Service Health:"
curl -s -o /dev/null -w "PostgreSQL: %{http_code}\n" http://localhost:5432 2>/dev/null || echo "PostgreSQL: Not HTTP"
curl -s -o /dev/null -w "PRM Service: %{http_code}\n" http://localhost:8007/health 2>/dev/null
curl -s -o /dev/null -w "Frontend: %{http_code}\n" http://localhost:3000 2>/dev/null
```

### View All Logs

```bash
# All container logs
docker compose logs --tail=100

# Specific service logs
docker compose logs -f prm-service --tail=100

# Backend Python logs
tail -f backend/logs/*.log

# Frontend Next.js logs
tail -f frontend/apps/prm-dashboard/.next/server/app-paths-manifest.json
```

---

## 2. Database Issues

### PostgreSQL Won't Start

**Symptom**: `postgres` container exits immediately

**Solution 1: Check for port conflict**
```bash
# Check if port 5432 is in use
lsof -i :5432

# Kill existing PostgreSQL
brew services stop postgresql  # macOS
sudo systemctl stop postgresql  # Linux

# Or use different port
# In docker-compose.yml, change: "5433:5432"
```

**Solution 2: Clear corrupted data**
```bash
# WARNING: This deletes all data!
docker compose down
docker volume rm healthtech-redefined_postgres_data
docker compose up -d postgres
```

**Solution 3: Check logs**
```bash
docker compose logs postgres
```

### Cannot Connect to Database

**Symptom**: `Connection refused` or `FATAL: password authentication failed`

**Solution 1: Verify connection string**
```bash
# Test connection
PGPASSWORD=healthtech psql -h localhost -U healthtech -d healthtech -c "SELECT 1"
```

**Solution 2: Check container is healthy**
```bash
docker compose ps postgres
# Should show: "running (healthy)"
```

**Solution 3: Wait for startup**
```bash
# PostgreSQL can take 10-30 seconds to be ready
docker compose logs -f postgres | grep "ready to accept connections"
```

### Migration Errors

**Symptom**: `alembic upgrade head` fails

**Solution 1: Check current state**
```bash
cd backend
source venv/bin/activate
alembic current
alembic history
```

**Solution 2: Fresh migration**
```bash
# Reset to base (WARNING: deletes all data)
alembic downgrade base
alembic upgrade head
```

**Solution 3: Fix stuck migration**
```bash
# Check alembic_version table
psql -h localhost -U healthtech -d healthtech -c "SELECT * FROM alembic_version;"

# Manually stamp version
alembic stamp head
```

---

## 3. Service Startup Issues

### Service Won't Start

**Symptom**: `uvicorn` exits with error

**Solution 1: Check Python environment**
```bash
cd backend
python --version  # Should be 3.11+
which python      # Should be in venv

# Recreate venv if needed
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Solution 2: Check environment variables**
```bash
# Verify .env exists
cat backend/.env

# Check for required vars
grep DATABASE_URL backend/.env
grep JWT_SECRET_KEY backend/.env
```

**Solution 3: Check import errors**
```bash
cd backend
python -c "from services.prm_service.main import app; print('Import OK')"
```

### Service Starts But Returns Errors

**Symptom**: HTTP 500 errors

**Solution 1: Check logs**
```bash
# If running with uvicorn
uvicorn services.prm_service.main:app --port 8007 --reload 2>&1 | tee app.log

# Check for tracebacks
grep -A 10 "Traceback" app.log
```

**Solution 2: Test health endpoint**
```bash
curl -v http://localhost:8007/health
```

**Solution 3: Check dependencies**
```bash
# Verify all services are running
curl http://localhost:5432  # PostgreSQL
curl http://localhost:6379  # Redis
curl http://localhost:9092  # Kafka
```

---

## 4. Port Conflicts

### Port Already in Use

**Symptom**: `Address already in use` or `EADDRINUSE`

**Solution 1: Find and kill process**
```bash
# Find process using port
lsof -i :3000

# Kill by PID
kill -9 <PID>

# Or kill by port (macOS/Linux)
kill -9 $(lsof -t -i:3000)
```

**Solution 2: Use different port**
```bash
# For backend
uvicorn services.prm_service.main:app --port 8017 --reload

# For frontend
PORT=3010 npm run dev

# In docker-compose.yml
ports:
  - "3010:3000"  # host:container
```

### Common Port Conflicts

| Port | Conflict With | Solution |
|------|---------------|----------|
| 3000 | Node.js apps, Grafana | Use 3010 for frontend |
| 5432 | Local PostgreSQL | Stop local service |
| 6379 | Local Redis | Stop local service |
| 8080 | Jenkins, Tomcat | Use 8090 |
| 9090 | Prometheus | Keep as-is |

---

## 5. Network Issues

### Services Can't Communicate

**Symptom**: Connection refused between services

**Solution 1: Check Docker network**
```bash
# List networks
docker network ls

# Inspect network
docker network inspect healthtech-network

# Verify containers are connected
docker network inspect healthtech-network | grep -A 5 "Containers"
```

**Solution 2: Use correct hostnames**
```bash
# Inside Docker: use service names
DATABASE_URL=postgresql://healthtech:healthtech@postgres:5432/healthtech

# Outside Docker: use localhost
DATABASE_URL=postgresql://healthtech:healthtech@localhost:5432/healthtech
```

**Solution 3: Recreate network**
```bash
docker compose down
docker network rm healthtech-network
docker compose up -d
```

### CORS Errors

**Symptom**: Browser shows CORS policy errors

**Solution 1: Check backend CORS config**
```python
# In FastAPI main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Solution 2: Update environment**
```bash
# backend/.env
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

---

## 6. Performance Issues

### Slow API Responses

**Solution 1: Check database performance**
```bash
# Connect to PostgreSQL
psql -h localhost -U healthtech -d healthtech

# Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
```

**Solution 2: Check Redis connectivity**
```bash
redis-cli -h localhost ping
redis-cli -h localhost info memory
```

**Solution 3: Profile Python code**
```bash
# Install profiler
pip install py-spy

# Profile running process
py-spy top --pid <PID>
```

### High Memory Usage

**Solution 1: Check container resources**
```bash
docker stats

# Limit in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G
```

**Solution 2: Check for memory leaks**
```bash
# Python memory profiling
pip install memory-profiler
python -m memory_profiler your_script.py
```

---

## 7. Authentication Issues

### JWT Token Errors

**Symptom**: `401 Unauthorized` or `Token expired`

**Solution 1: Verify JWT secret**
```bash
# Both frontend and backend must use same secret
grep JWT_SECRET backend/.env
grep JWT_SECRET frontend/apps/prm-dashboard/.env.local
```

**Solution 2: Check token expiration**
```bash
# Decode JWT (use jwt.io or)
python -c "
import jwt
token = 'YOUR_TOKEN_HERE'
print(jwt.decode(token, options={'verify_signature': False}))
"
```

**Solution 3: Clear browser storage**
```javascript
// In browser console
localStorage.clear()
sessionStorage.clear()
```

### Login Fails

**Solution 1: Check auth service**
```bash
curl -X POST http://localhost:8004/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test"}'
```

**Solution 2: Verify user exists**
```bash
psql -h localhost -U healthtech -d healthtech -c \
  "SELECT id, email, is_active FROM users WHERE email = 'test@example.com';"
```

---

## 8. Kafka Issues

### Kafka Won't Start

**Symptom**: Kafka container keeps restarting

**Solution 1: Check Zookeeper**
```bash
docker compose logs zookeeper
# Must show "binding to port 0.0.0.0/0.0.0.0:2181"
```

**Solution 2: Clear Kafka data**
```bash
docker compose down
docker volume rm healthtech-redefined_kafka_data
docker volume rm healthtech-redefined_zookeeper_data
docker compose up -d zookeeper kafka
```

**Solution 3: Check memory**
```bash
# Kafka needs at least 1GB RAM
docker stats kafka
```

### Messages Not Being Processed

**Solution 1: Check consumer lag**
```bash
# Using kafka-ui at http://localhost:8090
# Or via CLI:
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group healthtech-consumers
```

**Solution 2: Check topic exists**
```bash
docker compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --list
```

---

## 9. Frontend Issues

### Next.js Build Fails

**Symptom**: `npm run build` errors

**Solution 1: Clear cache**
```bash
cd frontend/apps/prm-dashboard
rm -rf .next
rm -rf node_modules
npm install
npm run build
```

**Solution 2: Check TypeScript errors**
```bash
npm run type-check
# or
npx tsc --noEmit
```

**Solution 3: Check environment variables**
```bash
# All NEXT_PUBLIC_* vars must be set at build time
cat .env.local | grep NEXT_PUBLIC
```

### Page Not Loading

**Solution 1: Check console errors**
```
Open browser DevTools (F12) > Console tab
```

**Solution 2: Check network requests**
```
DevTools > Network tab > Look for failed requests (red)
```

**Solution 3: Check API connectivity**
```bash
curl http://localhost:8007/health
```

---

## 10. Docker Issues

### Container Exits Immediately

**Solution 1: Check logs**
```bash
docker compose logs <service-name>
docker logs <container-id>
```

**Solution 2: Run interactively**
```bash
docker compose run --rm prm-service bash
# Then manually start: uvicorn main:app
```

### Out of Disk Space

**Solution 1: Clean up Docker**
```bash
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune -a

# Remove unused volumes (WARNING: data loss)
docker volume prune

# Full cleanup
docker system prune -a --volumes
```

**Solution 2: Check disk usage**
```bash
docker system df
```

### Permission Errors

**Symptom**: `Permission denied` in container

**Solution 1: Fix file ownership**
```bash
# Linux only
sudo chown -R $USER:$USER .
```

**Solution 2: Run as root (dev only)**
```yaml
# docker-compose.yml
services:
  prm-service:
    user: root
```

---

## Emergency Recovery

### Complete Reset (Development Only)

```bash
#!/bin/bash
# WARNING: This deletes ALL data!

echo "Stopping all containers..."
docker compose down --volumes --remove-orphans

echo "Removing all volumes..."
docker volume rm $(docker volume ls -q | grep healthtech) 2>/dev/null

echo "Removing network..."
docker network rm healthtech-network 2>/dev/null

echo "Cleaning Python..."
cd backend
rm -rf venv __pycache__ .pytest_cache

echo "Cleaning Node..."
cd ../frontend/apps/prm-dashboard
rm -rf node_modules .next

echo "Rebuilding..."
cd ../../../
./setup.sh

echo "Done! Run: docker compose up -d"
```

---

## Getting Help

1. **Check existing docs**: `docs/` folder
2. **Search issues**: GitHub Issues
3. **Community**: Discord/Slack channel
4. **Logs**: Always include relevant logs when asking for help

### Useful Debug Commands

```bash
# System info
uname -a
docker version
python --version
node --version

# Process info
ps aux | grep python
ps aux | grep node

# Network info
netstat -tlnp | grep LISTEN
ss -tlnp | grep LISTEN
```
