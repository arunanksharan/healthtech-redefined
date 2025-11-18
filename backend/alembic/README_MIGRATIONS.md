# Database Migrations with Alembic

This directory contains database migration scripts managed by Alembic.

## Prerequisites

1. PostgreSQL database running (via Docker Compose or local installation)
2. Python virtual environment activated
3. Environment variables configured (`.env` file)

## Setup Instructions

### 1. Start PostgreSQL Database

```bash
# Using Docker Compose (from project root)
docker-compose up -d postgres

# Wait for database to be ready
docker-compose ps postgres
```

### 2. Create Initial Migration

```bash
cd backend
source venv/bin/activate

# Generate initial migration from models
alembic revision --autogenerate -m "Initial schema"

# Review the generated migration in alembic/versions/
```

### 3. Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Verify migrations applied
alembic current
```

### 4. Seed Initial Data

```bash
# Run seed data script
python alembic/seed_data.py
```

This will create:
- Default tenant (ID: 00000000-0000-0000-0000-000000000001)
- 6 default roles (system_admin, tenant_admin, doctor, nurse, receptionist, patient)
- 30+ permissions
- Admin user (email: admin@healthtech.local, password: Admin@123)
- Default organization and location

## Common Commands

### Create New Migration

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new table"

# Create empty migration file
alembic revision -m "Custom migration"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Upgrade one revision forward
alembic upgrade +1
```

### Rollback Migrations

```bash
# Downgrade one revision
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>

# Downgrade to base (remove all migrations)
alembic downgrade base
```

### View Migration History

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic history --verbose
```

### Stamp Database

```bash
# Mark database as being at specific revision (without running migrations)
alembic stamp head

# Useful when starting with existing database
alembic stamp <revision_id>
```

## Migration Workflow

### Adding a New Model

1. Create or modify model in `backend/shared/database/models.py`
2. Generate migration:
   ```bash
   alembic revision --autogenerate -m "Add <model_name> model"
   ```
3. Review generated migration file in `alembic/versions/`
4. Apply migration:
   ```bash
   alembic upgrade head
   ```

### Modifying Existing Model

1. Update model in `backend/shared/database/models.py`
2. Generate migration:
   ```bash
   alembic revision --autogenerate -m "Update <model_name> - <description>"
   ```
3. Review migration - Alembic may not detect all changes (indexes, constraints, etc.)
4. Manually edit migration file if needed
5. Apply migration:
   ```bash
   alembic upgrade head
   ```

## Database Reset (Development Only)

```bash
# Drop all tables and reapply migrations
alembic downgrade base
alembic upgrade head
python alembic/seed_data.py
```

## Troubleshooting

### Migration Conflicts

If you encounter migration conflicts (multiple heads):

```bash
# View heads
alembic heads

# Merge branches
alembic merge -m "Merge migrations" <rev1> <rev2>
```

### Database Connection Errors

1. Check PostgreSQL is running:
   ```bash
   docker-compose ps postgres
   ```

2. Verify `.env` file has correct DATABASE_URL:
   ```
   DATABASE_URL=postgresql://healthtech:healthtech@localhost:5432/healthtech
   ```

3. Test connection:
   ```bash
   psql postgresql://healthtech:healthtech@localhost:5432/healthtech -c "SELECT 1;"
   ```

### Alembic Can't Find Models

If Alembic can't detect your models:

1. Ensure models are imported in `alembic/env.py`
2. Check `sys.path` is correctly set in `env.py`
3. Verify models are using `Base` from `shared.database.models`

### Out-of-Sync Database

If database is out of sync with migrations:

```bash
# Check current state
alembic current

# Manually stamp to correct revision
alembic stamp head

# Or rebuild from scratch (⚠️ data loss!)
alembic downgrade base
alembic upgrade head
```

## Production Considerations

1. **Always backup database before running migrations**
   ```bash
   pg_dump -U healthtech -d healthtech > backup_$(date +%Y%m%d).sql
   ```

2. **Test migrations on staging environment first**

3. **Review auto-generated migrations carefully**
   - Alembic may not detect all schema changes
   - Add custom migration code for complex changes
   - Test rollback migrations

4. **Use transactions** for data migrations
   - Alembic migrations run in transactions by default
   - For complex data migrations, test extensively

5. **Change default admin password**
   ```bash
   # After running seed_data.py in production
   # Log in and change password via Auth Service
   ```

## File Structure

```
alembic/
├── versions/           # Migration files (auto-generated)
│   └── <revision_id>_<description>.py
├── env.py             # Alembic environment configuration
├── script.py.mako     # Migration template
├── seed_data.py       # Initial data seeding script
└── README_MIGRATIONS.md  # This file
```

## Environment Variables

Required in `.env`:

```bash
DATABASE_URL=postgresql://healthtech:healthtech@localhost:5432/healthtech
```

Optional:
```bash
ALEMBIC_CONFIG=alembic.ini  # Custom config file path
```

## Quick Reference

| Command | Description |
|---------|-------------|
| `alembic revision --autogenerate -m "msg"` | Create new migration |
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Rollback one migration |
| `alembic current` | Show current revision |
| `alembic history` | Show migration history |
| `alembic stamp head` | Mark database as current |
| `python alembic/seed_data.py` | Load initial data |

## Support

For issues or questions:
1. Check Alembic documentation: https://alembic.sqlalchemy.org/
2. Review migration files in `alembic/versions/`
3. Check database logs: `docker-compose logs postgres`
