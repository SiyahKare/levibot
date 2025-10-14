# LeviBot Nightly AutoML — Cron Container
# Runs nightly model retraining at 03:00 UTC

FROM python:3.11-slim

# Install cron
RUN apt-get update && \
  apt-get install -y cron && \
  rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application code
COPY backend/src /app/backend/src
COPY scripts /app/scripts

# Create data directories
RUN mkdir -p /app/backend/data/models \
  /app/backend/data/raw \
  /app/backend/data/logs

# Set Python path
ENV PYTHONPATH=/app

# Create cron job: run at 03:00 UTC every day
RUN echo "0 3 * * * cd /app && /usr/local/bin/python -m backend.src.automl.nightly_retrain >> /var/log/levibot_nightly.log 2>&1" > /etc/cron.d/levibot-cron && \
  chmod 0644 /etc/cron.d/levibot-cron && \
  crontab /etc/cron.d/levibot-cron && \
  touch /var/log/levibot_nightly.log

# Run cron in foreground
CMD ["cron", "-f"]

