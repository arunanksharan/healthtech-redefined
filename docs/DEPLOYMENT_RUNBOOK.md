# PRM Service - Deployment Runbook

**Version:** 1.0
**Last Updated:** November 19, 2024
**Status:** Production Ready

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Docker Deployment](#docker-deployment)
4. [Production Deployment](#production-deployment)
5. [Database Migrations](#database-migrations)
6. [Monitoring & Health Checks](#monitoring--health-checks)
7. [Troubleshooting](#troubleshooting)
8. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

### Required Software
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (for containerized deployment)
- Git

### Required Credentials
- Twilio Account (WhatsApp & SMS)
- OpenAI API Key (Embeddings, Whisper)
- AWS Account (S3 Storage)
- N8N Workflow URL (optional)
- Sentry DSN (monitoring)

---

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourorg/healthtech-redefined.git
cd healthtech-redefined/backend/services/prm-service
```

### 2. Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
cd ../../  # Go to backend directory
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cd services/prm-service
cp .env.example .env
# Edit .env with your credentials
```

### 5. Set Up Database

```bash
# Start PostgreSQL (if not running)
# On macOS: brew services start postgresql
# On Linux: sudo systemctl start postgresql

# Create database
createdb prm_db

# Run migrations
cd ../../  # Go to backend directory
alembic upgrade head
```

### 6. Start Redis

```bash
# On macOS
brew services start redis

# On Linux
sudo systemctl start redis

# Or using Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### 7. Run Application

```bash
cd services/prm-service
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 8. Verify Installation

```bash
# Check health endpoint
curl http://localhost:8000/health

# Access API documentation
open http://localhost:8000/docs
```

---

## Docker Deployment

### Using Docker Compose (Recommended for Testing)

### 1. Configure Environment

```bash
cd backend/services/prm-service
cp .env.example .env
# Edit .env with production values
```

### 2. Build and Start Services

```bash
# Build images
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f prm-service
```

### 3. Run Migrations

```bash
# Execute migrations inside container
docker-compose exec prm-service alembic upgrade head
```

### 4. Verify Deployment

```bash
# Check service health
curl http://localhost:8000/health

# Check all containers
docker-compose ps

# Expected output:
# prm-service    running    0.0.0.0:8000->8000/tcp
# prm-postgres   running    0.0.0.0:5432->5432/tcp
# prm-redis      running    0.0.0.0:6379->6379/tcp
```

### 5. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Production Deployment

### Option 1: Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml prm

# Check services
docker service ls

# Scale services
docker service scale prm_prm-service=4

# Remove stack
docker stack rm prm
```

### Option 2: Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: prm-service
  labels:
    app: prm-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: prm-service
  template:
    metadata:
      labels:
        app: prm-service
    spec:
      containers:
      - name: prm-service
        image: ghcr.io/yourorg/prm-service:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: prm-secrets
              key: database-url
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: prm-service
spec:
  selector:
    app: prm-service
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

**Deploy to Kubernetes:**

```bash
# Create namespace
kubectl create namespace prm

# Create secrets
kubectl create secret generic prm-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=openai-api-key="sk-..." \
  -n prm

# Deploy application
kubectl apply -f k8s/deployment.yaml -n prm

# Check pods
kubectl get pods -n prm

# Check logs
kubectl logs -f deployment/prm-service -n prm

# Scale deployment
kubectl scale deployment prm-service --replicas=5 -n prm
```

### Option 3: AWS ECS/Fargate

```bash
# Create ECR repository
aws ecr create-repository --repository-name prm-service

# Build and push image
docker build -t prm-service .
docker tag prm-service:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/prm-service:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/prm-service:latest

# Create task definition (use AWS Console or CLI)
# Create ECS service
# Configure load balancer
```

---

## Database Migrations

### Creating Migrations

```bash
# Auto-generate migration from model changes
cd backend
alembic revision --autogenerate -m "Description of changes"

# Review generated migration file
# Edit if necessary: backend/alembic/versions/xxxxx_description.py

# Apply migration
alembic upgrade head
```

### Applying Migrations

```bash
# Check current version
alembic current

# Show migration history
alembic history

# Upgrade to latest
alembic upgrade head

# Upgrade to specific version
alembic upgrade <revision_id>

# Downgrade one version
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>
```

### Production Migration Checklist

- [ ] Test migration on staging environment
- [ ] Backup production database
- [ ] Review migration SQL (`alembic upgrade head --sql`)
- [ ] Plan rollback strategy
- [ ] Schedule maintenance window
- [ ] Apply migration
- [ ] Verify data integrity
- [ ] Monitor application logs
- [ ] Run smoke tests

---

## Monitoring & Health Checks

### Health Endpoint

```bash
# Basic health check
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2024-11-19T12:00:00Z"
}
```

### Prometheus Metrics

```bash
# Access Prometheus
open http://localhost:9090

# Key metrics to monitor:
# - prm_requests_total
# - prm_request_duration_seconds
# - prm_active_connections
# - prm_database_pool_size
```

### Grafana Dashboards

```bash
# Access Grafana
open http://localhost:3000

# Default credentials: admin / admin

# Import PRM dashboard:
# - Request rate
# - Error rate
# - Response time
# - Database connections
# - Redis hit rate
```

### Logging

```bash
# View application logs
docker-compose logs -f prm-service

# Or if running locally
tail -f logs/prm-service.log

# Log to Sentry (configured in .env)
# Errors automatically reported to Sentry dashboard
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Symptom:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Solutions:**
```bash
# Check PostgreSQL is running
pg_isready -h localhost -p 5432

# Verify DATABASE_URL in .env
echo $DATABASE_URL

# Test connection
psql $DATABASE_URL -c "SELECT 1;"

# Check firewall rules
sudo ufw status
```

#### 2. Redis Connection Failed

**Symptom:**
```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**Solutions:**
```bash
# Check Redis is running
redis-cli ping

# Verify REDIS_URL
echo $REDIS_URL

# Test connection
redis-cli -u $REDIS_URL ping

# Restart Redis
docker-compose restart redis
```

#### 3. Migration Conflicts

**Symptom:**
```
alembic.util.exc.CommandError: Target database is not up to date
```

**Solutions:**
```bash
# Check current version
alembic current

# Show pending migrations
alembic history

# Force to specific version (CAUTION!)
alembic stamp head

# Or manually resolve conflicts in alembic_version table
```

#### 4. Import Errors

**Symptom:**
```
ModuleNotFoundError: No module named 'shared'
```

**Solutions:**
```bash
# Ensure correct Python path
export PYTHONPATH=/path/to/healthtech-redefined/backend:$PYTHONPATH

# Verify installation
pip list | grep -i fastapi

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### 5. Port Already in Use

**Symptom:**
```
OSError: [Errno 48] Address already in use
```

**Solutions:**
```bash
# Find process using port 8000
lsof -ti:8000

# Kill process
kill -9 $(lsof -ti:8000)

# Or use different port
uvicorn main:app --port 8001
```

---

## Rollback Procedures

### Application Rollback

#### Docker Deployment

```bash
# Stop current version
docker-compose down

# Pull previous version
docker pull ghcr.io/yourorg/prm-service:previous-tag

# Update docker-compose.yml with previous tag

# Start previous version
docker-compose up -d

# Verify
curl http://localhost:8000/health
```

#### Kubernetes Deployment

```bash
# Rollback deployment
kubectl rollout undo deployment/prm-service -n prm

# Check rollout status
kubectl rollout status deployment/prm-service -n prm

# View rollout history
kubectl rollout history deployment/prm-service -n prm

# Rollback to specific revision
kubectl rollout undo deployment/prm-service --to-revision=2 -n prm
```

### Database Rollback

```bash
# Check current migration
alembic current

# Show migration history
alembic history

# Downgrade to previous version
alembic downgrade -1

# Or downgrade to specific version
alembic downgrade <revision_id>

# Verify downgrade
alembic current
```

### Emergency Rollback Checklist

- [ ] Identify issue (logs, metrics, user reports)
- [ ] Notify team
- [ ] Stop current deployment
- [ ] Restore previous application version
- [ ] Rollback database if necessary
- [ ] Verify rollback success
- [ ] Monitor closely for 30 minutes
- [ ] Post-mortem analysis

---

## Performance Tuning

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX idx_journeys_org_active ON journeys(org_id, is_active);
CREATE INDEX idx_appointments_patient_date ON appointments(patient_id, start_time);
CREATE INDEX idx_conversations_phone ON conversations(phone_number, created_at);

-- Vacuum and analyze
VACUUM ANALYZE;

-- Check slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### Redis Optimization

```bash
# Monitor Redis performance
redis-cli info stats

# Increase maxmemory if needed
redis-cli CONFIG SET maxmemory 2gb

# Set eviction policy
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

### Application Optimization

```python
# In main.py, increase workers
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Adjust based on: workers = (2 x CPU cores) + 1
# For 4 CPU cores: 9 workers
```

---

## Security Checklist

### Before Production

- [ ] Change all default passwords
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS/TLS
- [ ] Configure CORS properly
- [ ] Set up firewall rules
- [ ] Validate Twilio webhooks
- [ ] Enable rate limiting
- [ ] Set up Sentry for error tracking
- [ ] Review environment variables
- [ ] Encrypt sensitive data at rest
- [ ] Regular security audits
- [ ] Keep dependencies updated

---

## Maintenance Schedule

### Daily
- Monitor error rates in Sentry
- Check system health metrics
- Review application logs

### Weekly
- Database backup verification
- Security patch review
- Performance metrics review

### Monthly
- Dependency updates
- Security audit
- Capacity planning review
- Disaster recovery drill

---

## Support Contacts

### On-Call Team
- **Primary:** DevOps Team (devops@example.com)
- **Secondary:** Backend Team (backend@example.com)
- **Emergency:** CTO (cto@example.com)

### External Support
- **Twilio:** support.twilio.com
- **OpenAI:** help.openai.com
- **AWS:** aws.amazon.com/support

---

## Quick Reference

### Essential Commands

```bash
# Start development server
uvicorn main:app --reload

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=modules

# Build Docker image
docker build -t prm-service .

# Start with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Run migration
alembic upgrade head

# Check health
curl http://localhost:8000/health

# Access API docs
open http://localhost:8000/docs
```

---

**Document Status:** Ready for Production
**Last Reviewed:** November 19, 2024
**Next Review:** December 19, 2024
