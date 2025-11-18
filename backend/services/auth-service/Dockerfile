# Auth Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared code
COPY shared/ /app/shared/

# Copy service code
COPY services/auth-service/ /app/services/auth-service/

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8004/health')" || exit 1

# Run the service
CMD ["uvicorn", "services.auth_service.main:app", "--host", "0.0.0.0", "--port", "8004"]
