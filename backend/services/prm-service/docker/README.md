# PRM Service - Docker Setup

Complete Docker configuration for running the PRM (Patient Relationship Management) service independently.

## Quick Start

### Development Mode (with hot reload)

```bash
cd docker
make dev
```

Or manually:

```bash
cd docker
cp .env.example .env
docker compose -f docker-compose.dev.yml up -d
```

**Access Points:**
- API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)

### Production Mode

```bash
cd docker
make prod
```

### Full Stack (with Kafka, Monitoring)

```bash
cd docker
make full
```

Additional services:
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3002 (admin/admin)
- Kafka: localhost:9092

## Available Commands

```bash
make help          # Show all commands

# Development
make dev           # Start development environment
make tools         # Start dev + admin tools (pgAdmin, Redis Commander)
make webhooks      # Start dev + ngrok tunnel for Zoice callbacks

# Production
make prod          # Start production environment
make full          # Start full stack with Kafka & monitoring

# Testing
make test          # Run all tests in isolated environment

# Utilities
make logs          # Follow service logs
make shell         # Open shell in app container
make db-shell      # Open PostgreSQL shell
make redis-shell   # Open Redis CLI
make stop          # Stop all services
make clean         # Remove all containers and volumes
```

## Directory Structure

```
docker/
├── Dockerfile.prod          # Production build (multi-stage, optimized)
├── Dockerfile.dev           # Development build (hot reload)
├── Dockerfile.test          # Test runner build
├── docker-compose.yml       # Production compose
├── docker-compose.dev.yml   # Development compose
├── docker-compose.test.yml  # Test compose
├── docker-compose.full.yml  # Full stack compose
├── .env.example             # Environment template
├── Makefile                 # Helper commands
├── init-scripts/
│   ├── postgres/            # DB initialization SQL
│   └── redis/               # Redis configuration
├── monitoring/
│   ├── prometheus/          # Prometheus config
│   └── grafana/             # Grafana provisioning
├── nginx/                   # Reverse proxy config
├── mock-servers/            # Mock APIs for testing
└── scripts/                 # Helper scripts
```

## Zoice Voice AI Integration

The PRM service integrates with Zoice Voice AI (https://api2.zoice.ai) for telephony features.

### Setting up Webhooks for Development

1. Configure your Zoice API credentials in `.env`:

```env
ZOICE_BASE_URL=https://api2.zoice.ai
ZOICE_API_KEY=your-api-key
ZOICE_WEBHOOK_SECRET=your-webhook-secret
```

2. Set up ngrok for webhook tunneling:

```bash
# Add your ngrok auth token to .env
NGROK_AUTHTOKEN=your-ngrok-token

# Start with webhook tunnel
make webhooks
```

3. Configure the webhook URLs in Zoice dashboard:
   - Call Start: `https://<ngrok-url>/api/v1/prm/voice/webhook/call-start`
   - Call End: `https://<ngrok-url>/api/v1/prm/voice/webhook/call-end`
   - Transcription: `https://<ngrok-url>/api/v1/prm/voice/webhook/transcription`

### Zoice API Documentation

API docs available at: https://api2.zoice.ai/plivo/docs

## Configuration

### Required Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | JWT signing key | - |
| `POSTGRES_PASSWORD` | Database password | `prm_secure_pass` |
| `ZOICE_API_KEY` | Zoice API key | - |

### Optional Services

| Variable | Description |
|----------|-------------|
| `TWILIO_ACCOUNT_SID` | Twilio for SMS/WhatsApp |
| `OPENAI_API_KEY` | OpenAI for embeddings/STT |
| `SENTRY_DSN` | Error monitoring |

## Running Tests

```bash
# Run all tests
make test

# Test results available in:
# - ./test-results/junit.xml
# - ./coverage/index.html
```

## Troubleshooting

### Database connection issues

```bash
# Check if PostgreSQL is healthy
docker compose -f docker-compose.dev.yml ps postgres

# View database logs
docker compose -f docker-compose.dev.yml logs postgres
```

### Service won't start

```bash
# Check service logs
docker compose -f docker-compose.dev.yml logs prm-service

# Rebuild from scratch
make clean
make dev
```

### Port conflicts

Update port mappings in `.env`:

```env
APP_PORT=8001
POSTGRES_PORT=5434
REDIS_PORT=6380
```
