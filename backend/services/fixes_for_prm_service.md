Here is a complete **README** documenting every fix we implemented. You can save this as `PRM_SERVICE_SETUP.md` in your project folder to help your team (and future you) replicate this success.

***

# PRM Service - Setup & Troubleshooting Guide

**Date:** December 10, 2025
**Status:** ✅ Operational
**Service:** `backend/services/prm-service`

## 1. Overview
This document details the steps taken to successfully containerize and run the `prm-service`. The original build failed due to dependency conflicts, Docker context restrictions, and breaking changes in updated Python libraries.

## 2. Infrastructure Changes

### A. Docker Context & File Structure
**Issue:** The service could not build from the project root due to complex context paths, and the specific `Dockerfile` tried to access files outside its build context (e.g., `COPY ../../requirements.txt`).

**Fix:**
1.  Moved operations to run directly inside `backend/services/prm-service`.
2.  Manually copied necessary shared resources into the service directory:
    *   Copied `backend/requirements.txt` → `backend/services/prm-service/requirements.txt`
    *   Copied `backend/shared/` directory → `backend/services/prm-service/shared/`
3.  Created a standalone `docker-compose.yml` specific to this service stack (Postgres, Redis, Grafana, Prometheus).

### B. Dockerfile Updates
**Issue:** Permission errors (`[Errno 13] Permission denied`) occurred because dependencies were installed by `root` but executed by a non-privileged `prmuser`.

**Fix:**
Updated `backend/services/prm-service/Dockerfile`:
1.  Changed dependency installation path to global system paths (`/usr/local`) instead of user-specific paths (`/root/.local`) to ensure accessibility.
2.  Temporarily disabled the `USER prmuser` switch (running as root) to bypass complex file ownership issues during development.
3.  Updated `COPY` commands to use local files (`requirements.txt`) instead of relative parent paths.

## 3. Dependency Management

### A. "Dependency Hell" Resolution
**Issue:** The original `requirements.txt` contained conflicting versions (e.g., `httpx-mock` vs `pytest`, old `pydantic` vs new `fhir.resources`), causing `pip` to hang indefinitely.

**Fix:**
Replaced the version-locked requirements with a "clean" list, allowing `pip` to resolve the latest compatible versions automatically.
*   *Critical updates:* Unpinned `langchain`, `openai`, `fastapi`, and `pydantic`.
*   *Constraint added:* Added `fhir.resources>=7.1.0` to support Pydantic v2.

## 4. Codebase Refactoring

### A. Pydantic V2 Migration
**Issue:** The code used Pydantic v1 syntax (`regex=...`), but the new environment installed Pydantic v2, causing crash loops.

**Fix:**
*   **File:** `shared/database/tenant_service.py`
*   **Change:** Replaced `regex="^[a-z0-9-]+$"` with `pattern="^[a-z0-9-]+$"`.

### B. SQLAlchemy V2 Compatibility
**Issue:** The `StoredEvent` model used a column named `metadata`. SQLAlchemy v2.0+ reserves this keyword, causing a startup crash.

**Fix:**
*   **File:** `shared/database/models.py`
*   **Change:** Renamed the `metadata` column to `event_metadata` (or similar non-reserved name).

### C. Import Logic
**Issue:** `main.py` utilized relative imports (`from .schemas import ...`) which fail when the script is executed directly by Uvicorn.

**Fix:**
*   **File:** `main.py`
*   **Change:** Converted to absolute imports (e.g., `from schemas import ...`).

## 5. Environment & Ports

### A. Port Conflicts
**Issue:** Ports `3000` (Grafana) and `5432` (Postgres) clashed with local services and the frontend.

**Fix:**
Updated `docker-compose.yml` port mappings:
*   **Grafana:** Mapped to `3002:3000`
*   **Postgres:** Mapped to `5435:5432`
*   **Redis:** Mapped to `6380:6379` (if conflicts arise).

### B. Missing Configuration
**Issue:** `prometheus.yml` was missing, causing mount errors. Postgres crashed due to missing password variables.

**Fix:**
1.  Created a local `prometheus.yml` file.
2.  Configured `POSTGRES_PASSWORD` and `DATABASE_URL` with valid credentials in `docker-compose.yml` (or `.env`).

## 6. How to Run (Quick Start)

1.  **Navigate to directory:**
    ```bash
    cd backend/services/prm-service
    ```
2.  **Start Services:**
    ```bash
    docker-compose up -d --build
    ```
3.  **Initialize Database (First Run Only):**
    ```bash
    docker exec -it prm-service alembic upgrade head
    ```
4.  **Access:**
    *   **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)
    *   **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
    *   **Grafana:** [http://localhost:3002](http://localhost:3002)

***