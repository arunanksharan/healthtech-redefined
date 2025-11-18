# PRM Dashboard - Deployment Guide

Complete guide for deploying the PRM Dashboard to production and staging environments.

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Deployment Methods](#deployment-methods)
5. [CI/CD Pipeline](#cicd-pipeline)
6. [Database Migrations](#database-migrations)
7. [Monitoring & Observability](#monitoring--observability)
8. [Security Checklist](#security-checklist)
9. [Rollback Procedures](#rollback-procedures)
10. [Post-Deployment](#post-deployment)
11. [Troubleshooting](#troubleshooting)

---

## Deployment Overview

### Architecture

```
┌─────────────┐      ┌──────────────┐      ┌────────────┐
│   Users     │ ───> │  Load        │ ───> │  Next.js   │
│  (Browser)  │      │  Balancer    │      │  App       │
└─────────────┘      └──────────────┘      └────────────┘
                                                  │
                                                  ├─> API Backend
                                                  ├─> Redis Cache
                                                  └─> PostgreSQL DB
```

### Deployment Platforms Supported

1. **Vercel** (Recommended for Next.js)
2. **Docker + Kubernetes**
3. **AWS ECS/Fargate**
4. **Google Cloud Run**
5. **Azure App Service**

---

## Prerequisites

### Required Tools

- Node.js 18+ LTS
- Docker (for containerized deployment)
- kubectl (for Kubernetes deployment)
- Git
- npm or yarn

### Required Accounts & Services

- GitHub account (for CI/CD)
- Vercel account (if using Vercel)
- Cloud provider account (AWS/GCP/Azure)
- Sentry account (for error tracking)
- OpenAI API key
- Email service (SendGrid/AWS SES)
- SMS service (Twilio)
- WhatsApp Business API

### Environment Variables

See `.env.production.template` for all required variables.

**Critical Variables:**
```bash
NEXT_PUBLIC_API_URL=https://api.healthtech.com/api/v1
JWT_SECRET=<32-char-secret>
OPENAI_API_KEY=sk-...
ENCRYPTION_KEY=<32-char-key>
```

---

## Environment Setup

### 1. Production Environment

#### Vercel Setup

**Step 1: Install Vercel CLI**
```bash
npm i -g vercel
```

**Step 2: Login to Vercel**
```bash
vercel login
```

**Step 3: Link Project**
```bash
cd frontend/apps/prm-dashboard
vercel link
```

**Step 4: Set Environment Variables**
```bash
# Set via Vercel dashboard or CLI
vercel env add NEXT_PUBLIC_API_URL production
vercel env add JWT_SECRET production
# ... repeat for all required variables
```

**Step 5: Deploy**
```bash
vercel --prod
```

#### Docker Deployment

**Step 1: Build Image**
```bash
docker build -t prm-dashboard:latest \
  --build-arg NEXT_PUBLIC_API_URL=https://api.healthtech.com/api/v1 \
  --build-arg NEXT_PUBLIC_WS_URL=wss://api.healthtech.com/ws \
  ./frontend/apps/prm-dashboard
```

**Step 2: Run Container**
```bash
docker run -d \
  -p 3000:3000 \
  --name prm-dashboard \
  --env-file .env.production \
  prm-dashboard:latest
```

**Step 3: Verify**
```bash
curl http://localhost:3000/api/health
```

#### Kubernetes Deployment

**Step 1: Create Namespace**
```bash
kubectl create namespace prm-production
```

**Step 2: Create Secrets**
```bash
kubectl create secret generic prm-secrets \
  --from-literal=JWT_SECRET='your-secret' \
  --from-literal=OPENAI_API_KEY='sk-...' \
  -n prm-production
```

**Step 3: Apply Deployment**
```bash
kubectl apply -f k8s/production/deployment.yaml
kubectl apply -f k8s/production/service.yaml
kubectl apply -f k8s/production/ingress.yaml
```

**Step 4: Verify**
```bash
kubectl get pods -n prm-production
kubectl logs -f deployment/prm-dashboard -n prm-production
```

### 2. Staging Environment

Follow same steps as production but use:
- `.env.staging` variables
- `staging` namespace (Kubernetes)
- Staging Vercel project
- `staging` tag (Docker)

---

## Deployment Methods

### Method 1: Vercel (Recommended)

**Pros:**
- Automatic SSL
- Global CDN
- Zero-config deployment
- Preview deployments for PRs
- Automatic scaling

**Cons:**
- Vendor lock-in
- Can be expensive at scale

**Deployment:**
```bash
# Automatic via GitHub integration
# Or manual:
vercel --prod
```

### Method 2: Docker

**Pros:**
- Portable
- Consistent across environments
- Full control
- Works with any cloud provider

**Cons:**
- More setup required
- Need to manage infrastructure

**Deployment:**
```bash
# Using docker-compose
docker-compose -f docker-compose.prod.yml up -d

# Or standalone
docker run -d -p 3000:3000 --env-file .env.production prm-dashboard:latest
```

### Method 3: Kubernetes

**Pros:**
- Auto-scaling
- High availability
- Self-healing
- Production-grade

**Cons:**
- Complex setup
- Requires K8s knowledge
- Higher operational overhead

**Deployment:**
```bash
# Apply manifests
kubectl apply -f k8s/production/

# Rolling update
kubectl set image deployment/prm-dashboard prm-dashboard=prm-dashboard:v1.2.0

# Check rollout status
kubectl rollout status deployment/prm-dashboard
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

**1. CI Workflow** (`.github/workflows/ci.yml`)
- Runs on: Every push and PR
- Steps:
  - Lint and format check
  - Security scan
  - Unit tests
  - E2E tests
  - Build verification
  - Docker build test

**2. CD Production** (`.github/workflows/cd-production.yml`)
- Runs on: Push to `main` or version tags
- Steps:
  - Pre-deployment checks
  - Build Docker image
  - Deploy to Vercel
  - Post-deployment verification
  - Create GitHub release

**3. CD Staging** (`.github/workflows/cd-staging.yml`)
- Runs on: Push to `develop`
- Steps:
  - Run tests
  - Deploy to Vercel staging
  - Verify deployment

### Setting Up CI/CD

**Step 1: Configure Secrets**

In GitHub repository settings > Secrets:

```
VERCEL_TOKEN=<vercel-token>
VERCEL_ORG_ID=<org-id>
VERCEL_PROJECT_ID=<project-id>
PROD_API_URL=https://api.healthtech.com/api/v1
PROD_WS_URL=wss://api.healthtech.com/ws
SLACK_WEBHOOK=<webhook-url>
```

**Step 2: Enable Workflows**

Workflows run automatically on push/PR.

**Step 3: Monitor Workflows**

- GitHub Actions tab shows all workflow runs
- Notifications sent to Slack on deployment

### Manual Deployment

To deploy manually from local machine:

```bash
# Production
git checkout main
git pull origin main
npm run deploy:production

# Staging
git checkout develop
git pull origin develop
npm run deploy:staging
```

---

## Database Migrations

### Migration Strategy

**Zero-Downtime Migrations:**
1. Deploy backward-compatible schema changes first
2. Deploy application code
3. Remove old schema (if needed)

### Running Migrations

**Production:**
```bash
# SSH into database server or use migration tool
npm run migrate:production

# Or using Docker
docker exec -it prm-backend npm run migrate
```

**Verify:**
```bash
# Check migration status
npm run migrate:status

# Should show all migrations applied
```

### Rollback Migrations

```bash
# Rollback last migration
npm run migrate:rollback

# Rollback to specific version
npm run migrate:rollback --to=20240115000000
```

---

## Monitoring & Observability

### Health Checks

**Endpoint:** `GET /api/health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-11-19T12:00:00Z",
  "uptime": 3600,
  "version": "1.0.0",
  "checks": [
    {"name": "environment", "status": "pass"},
    {"name": "backend_api", "status": "pass", "responseTime": 150},
    {"name": "memory", "status": "pass"}
  ]
}
```

### Sentry Setup

**1. Create Sentry Project**
- Go to sentry.io
- Create new project (Next.js)
- Get DSN

**2. Configure**
```bash
# Add to .env.production
NEXT_PUBLIC_SENTRY_DSN=https://...@sentry.io/...
```

**3. Verify**
```bash
# Trigger test error
curl -X POST https://app.healthtech.com/api/test-error
```

### Analytics

**Google Analytics:**
```bash
NEXT_PUBLIC_ANALYTICS_ID=G-XXXXXXXXXX
```

**Vercel Analytics:**
- Enable in Vercel dashboard
- Automatically tracks Core Web Vitals

### Logging

**Structured Logging:**
```typescript
import { logger } from '@/lib/logger';

logger.info('User logged in', { userId: user.id });
logger.error('API call failed', { error, endpoint });
```

**Log Aggregation:**
- CloudWatch (AWS)
- Stackdriver (GCP)
- Azure Monitor
- Datadog

---

## Security Checklist

### Pre-Deployment

- [ ] All environment variables in `.env.production`
- [ ] No secrets in code or repository
- [ ] `NEXT_TELEMETRY_DISABLED=1` in production
- [ ] Security headers configured (HSTS, CSP, etc.)
- [ ] HTTPS enforced
- [ ] JWT secret is 32+ characters
- [ ] Encryption keys rotated
- [ ] Rate limiting configured
- [ ] CORS configured correctly
- [ ] Security scan passed (`npm audit`)
- [ ] Dependencies updated
- [ ] No debug logs in production code

### Post-Deployment

- [ ] Health check returns 200
- [ ] SSL certificate valid
- [ ] Security headers present
- [ ] No errors in Sentry
- [ ] Logs flowing to aggregation service
- [ ] Monitoring dashboards updated
- [ ] Backup jobs running
- [ ] Audit logging working

---

## Rollback Procedures

### Vercel Rollback

**Option 1: Via Dashboard**
1. Go to Vercel dashboard
2. Select deployment
3. Click "Promote to Production"

**Option 2: Via CLI**
```bash
# List deployments
vercel ls

# Rollback to specific deployment
vercel rollback <deployment-url>
```

### Docker Rollback

```bash
# Pull previous version
docker pull prm-dashboard:v1.0.0

# Stop current
docker stop prm-dashboard

# Start previous version
docker run -d --name prm-dashboard prm-dashboard:v1.0.0
```

### Kubernetes Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/prm-dashboard

# Rollback to specific revision
kubectl rollout undo deployment/prm-dashboard --to-revision=2

# Check rollout status
kubectl rollout status deployment/prm-dashboard
```

### Database Rollback

```bash
# Rollback migrations
npm run migrate:rollback

# Restore from backup
pg_restore -d prm_production backup_20241119.dump
```

---

## Post-Deployment

### Verification Checklist

**Immediate (0-5 minutes):**
- [ ] Health check returns 200
- [ ] Homepage loads
- [ ] Can log in
- [ ] Dashboard loads
- [ ] AI Assistant responds
- [ ] No errors in browser console
- [ ] No errors in Sentry

**Short-term (5-30 minutes):**
- [ ] All critical user flows work
- [ ] API response times normal
- [ ] Error rate within acceptable range
- [ ] Memory usage stable
- [ ] CPU usage normal
- [ ] Database queries performing well

**Medium-term (1-24 hours):**
- [ ] No increase in error rate
- [ ] User feedback positive
- [ ] Performance metrics stable
- [ ] No memory leaks
- [ ] Logs normal
- [ ] Backups running

### Smoke Tests

Run automated smoke tests:

```bash
npm run test:smoke:production
```

Or manual:
```bash
# Test health endpoint
curl https://app.healthtech.com/api/health

# Test homepage
curl https://app.healthtech.com

# Test login (with credentials)
curl -X POST https://app.healthtech.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'
```

### Monitoring Dashboards

**Monitor:**
- Sentry: Error rates and issues
- Vercel: Performance and analytics
- CloudWatch/Stackdriver: Infrastructure metrics
- PagerDuty: Alerts and incidents

**Key Metrics:**
- Error rate: < 0.1%
- Response time (P95): < 1000ms
- Availability: > 99.9%
- CPU usage: < 70%
- Memory usage: < 80%

### User Communication

**Announce Deployment:**
```
Subject: PRM Dashboard Update - [Version] Deployed

The PRM Dashboard has been updated to version [X.X.X].

New Features:
- [Feature 1]
- [Feature 2]

Bug Fixes:
- [Fix 1]
- [Fix 2]

If you experience any issues, please contact support@healthtech.com

- The HealthTech Team
```

---

## Troubleshooting

### Common Issues

**1. Deployment Failed**

**Symptoms:**
- Build fails
- Deployment stuck
- Application won't start

**Solutions:**
```bash
# Check build logs
vercel logs

# Verify environment variables
vercel env ls

# Check Docker logs
docker logs prm-dashboard

# Check Kubernetes pods
kubectl describe pod <pod-name>
kubectl logs <pod-name>
```

**2. Health Check Failing**

**Symptoms:**
- `/api/health` returns 503
- Load balancer marks instance unhealthy

**Solutions:**
```bash
# Check application logs
tail -f /var/log/prm-dashboard/app.log

# Verify backend API connectivity
curl https://api.healthtech.com/api/v1/health

# Check environment variables
env | grep NEXT_PUBLIC_API_URL
```

**3. High Memory Usage**

**Symptoms:**
- Memory usage > 90%
- Application crashes
- Slow performance

**Solutions:**
```bash
# Restart application
kubectl rollout restart deployment/prm-dashboard

# Increase memory limits (Kubernetes)
kubectl set resources deployment prm-dashboard --limits=memory=2Gi

# Check for memory leaks in logs
```

**4. Database Connection Issues**

**Symptoms:**
- API errors
- Timeout errors
- Connection refused

**Solutions:**
```bash
# Verify database is running
pg_isready -h db-host -p 5432

# Check connection string
echo $DATABASE_URL

# Verify network connectivity
telnet db-host 5432

# Check connection pool
# Max connections should be sufficient
```

### Emergency Contacts

**During Deployment:**
- DevOps Lead: devops@healthtech.com
- CTO: cto@healthtech.com
- On-call Engineer: oncall@healthtech.com

**Escalation:**
1. Try rollback first
2. Contact DevOps lead
3. If critical, page on-call
4. Notify CTO if widespread impact

---

## Deployment Schedule

**Production:**
- **When:** First Sunday of each month, 2-4 AM EST
- **Frequency:** Monthly (major releases)
- **Hot fixes:** As needed, with approval

**Staging:**
- **When:** Any time
- **Frequency:** Daily/on-demand
- **Purpose:** Testing before production

**Notification:**
- 1 week advance notice for major releases
- 24 hours for minor releases
- Immediate for critical security patches

---

## Checklist

### Pre-Deployment

- [ ] All tests passing
- [ ] Security scan clean
- [ ] Environment variables configured
- [ ] Database migrations ready
- [ ] Backup created
- [ ] Rollback plan documented
- [ ] Team notified
- [ ] Monitoring dashboards ready
- [ ] On-call engineer identified
- [ ] Documentation updated

### During Deployment

- [ ] Maintenance mode enabled (if applicable)
- [ ] Migrations applied
- [ ] Application deployed
- [ ] Health checks passing
- [ ] Smoke tests executed
- [ ] Error rates normal
- [ ] Performance metrics normal

### Post-Deployment

- [ ] Maintenance mode disabled
- [ ] Users notified
- [ ] Monitoring for 1 hour
- [ ] Documentation updated
- [ ] Release notes published
- [ ] Team debriefed
- [ ] Lessons learned documented

---

**Last Updated:** November 19, 2024
**Version:** 1.0
**For:** DevOps Engineers, Site Reliability Engineers

**Questions?** Contact devops@healthtech.com
