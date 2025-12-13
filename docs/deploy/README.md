# HealthTech Platform - Deployment Documentation

This folder contains comprehensive deployment documentation for the HealthTech Patient Relationship Management (PRM) platform.

## Quick Start

```bash
# Start development environment
./docs/deploy/scripts/start-dev.sh

# Stop all services
./docs/deploy/scripts/stop-dev.sh

# Stop and remove all data
./docs/deploy/scripts/stop-dev.sh --clean
```

## Documentation Structure

```
docs/deploy/
├── README.md                    # This file
├── DEPLOYMENT-GUIDE.md          # Complete step-by-step deployment guide
├── PORT-REFERENCE.md            # All port allocations and mappings
├── TROUBLESHOOTING.md           # Common issues and solutions
│
├── env-templates/               # Environment variable templates
│   ├── .env.backend.example     # Backend service configuration
│   ├── .env.frontend.example    # Frontend application configuration
│   └── .env.production.example  # Production environment template
│
├── docker/                      # Docker Compose configurations
│   ├── docker-compose.dev.yml   # Development environment
│   └── docker-compose.production.yml  # Production environment
│
└── scripts/                     # Automation scripts
    ├── start-dev.sh             # Start development environment
    └── stop-dev.sh              # Stop all services
```

## Key Documents

| Document | Description |
|----------|-------------|
| [DEPLOYMENT-GUIDE.md](./DEPLOYMENT-GUIDE.md) | Complete deployment instructions |
| [PORT-REFERENCE.md](./PORT-REFERENCE.md) | Port allocations for all services |
| [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) | Solutions to common problems |

## Port Summary

| Service | Port | URL |
|---------|------|-----|
| Frontend (PRM Dashboard) | 3000 | http://localhost:3000 |
| PRM Service API | 8007 | http://localhost:8007 |
| PostgreSQL | 5432 | localhost:5432 |
| Redis | 6379 | localhost:6379 |
| Kafka | 9092 | localhost:9092 |
| Grafana | 3001 | http://localhost:3001 |
| Kafka UI | 8090 | http://localhost:8090 |
| pgAdmin | 5050 | http://localhost:5050 |

## Environment Setup

1. Copy environment templates:
   ```bash
   cp docs/deploy/env-templates/.env.backend.example backend/.env
   cp docs/deploy/env-templates/.env.frontend.example frontend/apps/prm-dashboard/.env.local
   ```

2. Update with your API keys:
   - OpenAI API key (required for AI features)
   - LiveKit credentials (required for video calls)
   - Twilio credentials (required for SMS/WhatsApp)
   - AWS credentials (required for file storage)

## Support

- See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for common issues
- Check service logs: `docker compose logs <service-name>`
- Full documentation: [../docs/](../)
