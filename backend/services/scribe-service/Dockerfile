# Scribe Service Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared code
COPY shared/ /app/shared/

# Copy service code
COPY services/scribe-service/ /app/services/scribe-service/

# Set Python path
ENV PYTHONPATH=/app

# LLM Configuration (can be overridden via environment variables)
ENV LLM_PROVIDER=openai
ENV LLM_MODEL=gpt-4
ENV LLM_TEMPERATURE=0.1

# Expose port
EXPOSE 8008

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8008/health')" || exit 1

# Run the service
CMD ["uvicorn", "services.scribe_service.main:app", "--host", "0.0.0.0", "--port", "8008"]
