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
COPY backend/requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
  pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/src ./src

# Create necessary directories
RUN mkdir -p ./data/models \
  ./data/logs \
  ./data/cache

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Default command (override in docker-compose)
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

