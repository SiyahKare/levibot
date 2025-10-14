FROM python:3.11-slim

LABEL maintainer="LeviBot Team"
LABEL description="Enterprise AI Signals Platform - Core Services"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  g++ \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY backend/requirements.txt ./requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
  pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY apps/ ./apps/

# Create necessary directories
RUN mkdir -p /app/backend/data/models \
  /app/backend/data/logs \
  /app/backend/data/cache

# Expose Prometheus metrics ports
EXPOSE 9100 9101

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:9100/metrics', timeout=5)" || exit 1

# Default command (override in docker-compose)
CMD ["python", "-m", "apps.signal_engine"]

