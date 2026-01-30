# PRM Dashboard - Docker Setup

This document explains how to run the PRM Dashboard using Docker.

## Quick Start

### 1. Setup Environment

```bash
# Copy the docker environment template
make setup
# or manually:
cp .env.docker .env

# Edit .env with your configuration
nano .env
```

### 2. Choose Your Setup

| Command | Description |
|---------|-------------|
| `make dev` | Development mode with hot-reload |
| `make up` | Standalone frontend only |
| `make full` | Full stack (frontend + backend + database) |

## Docker Files Overview

| File | Purpose |
|------|---------|
| `Dockerfile` | Production multi-stage build |
| `Dockerfile.dev` | Development with hot-reload |
| `docker-compose.yml` | Standalone frontend |
| `docker-compose.dev.yml` | Development mode |
| `docker-compose.full.yml` | Full stack with all services |
| `.env.docker` | Environment template |

## Running Modes

### Development Mode
Best for local development with hot-reload:

```bash
make dev

# View logs
make dev-logs

# Stop
make dev-down
```

The development server runs at **http://localhost:3000** with hot-reload enabled.

### Standalone Frontend
Run just the frontend (requires backend running separately):

```bash
# Start
make up

# View logs
make logs

# Stop
make down
```

### Full Stack
Run the complete PRM application:

```bash
# Start all services
make full

# View logs
make full-logs

# Stop
make full-down
```

Services started:
- **prm-dashboard** - Frontend at http://localhost:3000
- **prm-service** - Backend API at http://localhost:8000
- **postgres** - PostgreSQL at localhost:5433
- **redis** - Redis at localhost:6379

### Optional Profiles

```bash
# With Nginx reverse proxy
make full-nginx

# With monitoring (Prometheus + Grafana)
make monitoring

# All services
make full-all
```

## Configuration

### Environment Variables

Key variables to configure in `.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://prm-service:8000` |
| `OPENAI_API_KEY` | OpenAI API key for AI features | - |
| `ZOICE_API_KEY` | Zoice Voice AI API key | - |
| `LIVEKIT_API_KEY` | LiveKit API key for voice | - |
| `POSTGRES_PASSWORD` | Database password | `postgres` |

### Zoice Voice AI Integration

The PRM Dashboard integrates with Zoice Voice AI at `https://api2.zoice.ai`. Configure:

```env
# Backend uses these to proxy Zoice API calls
ZOICE_API_URL=https://api2.zoice.ai
ZOICE_API_KEY=your_zoice_api_key
ZOICE_WEBHOOK_SECRET=your_webhook_secret

# Frontend (if direct API calls needed)
NEXT_PUBLIC_ZOICE_API_URL=https://api2.zoice.ai
```

The Zoice API is proxied through the backend at `/api/v1/prm/admin/zoice/*`.

## Useful Commands

### Health Check
```bash
make health
```

### Database Access
```bash
# PostgreSQL shell
make db-shell

# Run migrations
make db-migrate
```

### Shell Access
```bash
# Frontend container
make shell

# Backend container (full stack only)
make full-shell-backend
```

### Cleanup
```bash
# Remove containers and local images
make clean

# Full cleanup including volumes
make clean-all
```

## Port Mapping

| Service | Internal Port | External Port |
|---------|---------------|---------------|
| prm-dashboard | 3000 | 3000 |
| prm-service | 8000 | 8000 |
| postgres | 5432 | 5433 |
| redis | 6379 | 6379 |
| prometheus | 9090 | 9090 |
| grafana | 3000 | 3002 |
| nginx | 80/443 | 80/443 |

## Network

All services connect through the `prm-network` bridge network. Service names can be used as hostnames within Docker (e.g., `http://prm-service:8000`).

## Troubleshooting

### Build Fails
```bash
# Clean build
docker compose build --no-cache
```

### Container Not Starting
```bash
# Check logs
docker compose logs prm-dashboard

# Check container status
docker compose ps
```

### Connection Refused to Backend
Ensure the backend is healthy:
```bash
curl http://localhost:8000/health
```

### Database Connection Issues
```bash
# Check postgres logs
docker compose -f docker-compose.full.yml logs postgres

# Verify connection
docker compose -f docker-compose.full.yml exec postgres pg_isready
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx (Optional)                      │
│                     Port 80/443                              │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┴───────────────┐
        │                               │
        ▼                               ▼
┌───────────────────┐         ┌───────────────────┐
│   PRM Dashboard   │         │   PRM Service     │
│   (Next.js)       │◄───────►│   (FastAPI)       │
│   Port 3000       │         │   Port 8000       │
└───────────────────┘         └─────────┬─────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
            ┌───────────┐       ┌───────────┐       ┌───────────┐
            │ PostgreSQL│       │   Redis   │       │  Zoice AI │
            │ Port 5432 │       │ Port 6379 │       │ External  │
            └───────────┘       └───────────┘       └───────────┘
```

## Production Deployment

For production:

1. Use proper secrets management
2. Enable SSL in Nginx
3. Set `NODE_ENV=production`
4. Configure proper database credentials
5. Set up monitoring with the `with-monitoring` profile
6. Use external managed services for PostgreSQL and Redis if needed
