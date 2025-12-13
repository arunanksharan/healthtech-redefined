# PRM Service (Backend)

The Patient Relationship Management (PRM) Service is the core backend for the HealthTech dashboard. It handles patient data, journeys, communications, and tickets.

## 🚀 Quick Start (Docker)

The easiest way to run the service is using Docker Compose.

1.  **Configure Environment**:
    ```bash
    cp .env.example .env
    ```
    (Adjust credentials in `.env` if needed, but defaults work out-of-the-box).

2.  **Start Services**:
    ```bash
    docker compose up -d
    ```
    This starts:
    -   `prm-service` (FastAPI backend) on `http://localhost:8000`
    -   `healthtech-postgres` (Database) on port `5433` (external) / `5432` (internal)
    -   `prm-redis` (Cache) on port `6379`
    -   `prm-grafana` & `prm-prometheus` (Monitoring)

3.  **Access Documentation**:
    -   Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
    -   ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 💻 Local Development Setup

If you want to run the FastAPI app locally (for hot-reloading) while keeping the database in Docker.

### 1. Prerequisites
-   Python 3.11+
-   Docker Desktop

### 2. Start Database Only
Start the database and redis containers:
```bash
docker compose up -d postgres redis
```
*Note: The database will act as 'localhost:5433' on your machine.*

### 3. Install Dependencies
```bash
# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate # Mac/Linux

# Install requirements
pip install -r requirements.txt
```

### 4. Run the Application
Use the helper script to run the app with the correct local database connection string:

**Windows (PowerShell)**:
```powershell
.\run_dev.ps1
```

**Mac/Linux**:
```bash
export DATABASE_URL="postgresql://healthtech:healthtech@127.0.0.1:5433/healthtech"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

---

## 🗄️ Database Initialization

The application automatically checks and creates tables on startup. However, you can manually initialize the schema if needed.

**Run from `backend` root:**
```bash
python create_schema.py
```

## 🌱 Database Seeding

Populate the database with sample data for development.

1.  **Ensure Virtual Environment is Active**.
2.  **Core Data (Run from `backend` root)**:
    This script initializes Tenants, Users, and Patients.
    ```bash
    cd ../../
    python seed_database.py
    cd services/prm-service
    ```

3.  **Service Data (Run from `prm-service` directory)**:
    These scripts populate service-specific data like tickets and messages.
    ```bash
    python seed_tickets.py
    python seed_journey_instances.py
    python seed_communications.py
    ```

---

## 🛠️ Troubleshooting

-   **Port Conflicts**: Ensure port `8000` is free. If running via Docker, make sure you aren't also running `uvicorn` locally on the same port.
-   **Database Connection Refused**:
    -   If running locally, ensure you use port `5433`.
    -   If running in Docker, ensure you use host `postgres` and port `5432`.
    -   Check container status: `docker ps`.
