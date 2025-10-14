FROM python:3.11-slim

LABEL maintainer="LeviBot Team"
LABEL description="Enterprise AI Signals Platform - Telegram Bot"

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
  pip install --no-cache-dir -r requirements.txt && \
  pip install --no-cache-dir python-telegram-bot

# Copy application code
COPY backend/ ./backend/
COPY apps/ ./apps/

# Health check (check if process is running)
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
  CMD pgrep -f telegram_bot || exit 1

# Run Telegram bot
CMD ["python", "-m", "apps.telegram_bot"]

