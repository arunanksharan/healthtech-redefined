# Project Commit Message Convention

All commits in this project MUST follow the detailed, professional format outlined below.

## Format Structure

```text
<type>(EPIC-<ID>): <Short Summary>

- <High-level change 1>
- <High-level change 2>
...

Features:
- <Detailed Feature 1>
- <Detailed Feature 2>
...

Fixes:
- <Fix 1>
- <Fix 2>
...
```

## Example

```text
feat(EPIC-024): Implement Production Readiness module

- Add production models with 21 enums and 23 SQLAlchemy models
- Implement infrastructure service for multi-AZ resource management
- Add monitoring service with metrics, dashboards, SLO/SLI tracking
- Create alerting service with incidents, on-call, escalation

Features:
- Infrastructure resource tracking with IaC support
- Auto-scaling configuration management
- Network configuration with WAF/DDoS protection
- Prometheus metrics and Grafana dashboards
- Health checks with liveness/readiness probes

Fixes:
- Resolved race condition in status updates
- Fixed database connection timeout
```

## Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools and libraries such as documentation generation
