#!/bin/bash
# Daily backup script for production data

set -e

BACKUP_DIR="backend/data/backup"
DATE=$(date +%F)
RETENTION_DAYS=7

echo "🗄️  LeviBot Daily Backup - $DATE"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# 1. DuckDB analytics
if [ -f backend/data/analytics.duckdb ]; then
    echo "Backing up DuckDB..."
    duckdb backend/data/analytics.duckdb ".backup '$BACKUP_DIR/analytics_$DATE.duckdb'"
    gzip -f "$BACKUP_DIR/analytics_$DATE.duckdb"
    echo "✓ DuckDB backup: $BACKUP_DIR/analytics_$DATE.duckdb.gz"
fi

# 2. Engine logs (compress and move to backup)
if ls backend/data/logs/engine-*.jsonl 1> /dev/null 2>&1; then
    echo "Archiving engine logs..."
    find backend/data/logs -name "engine-*.jsonl" -mtime +1 -exec gzip -f {} \;
    find backend/data/logs -name "*.jsonl.gz" -exec mv {} "$BACKUP_DIR/" \;
    echo "✓ Engine logs archived"
fi

# 3. Model registry
if [ -f backend/data/registry/model_registry.json ]; then
    echo "Backing up model registry..."
    cp backend/data/registry/model_registry.json "$BACKUP_DIR/model_registry_$DATE.json"
    echo "✓ Model registry backed up"
fi

# 4. Config snapshots
if [ -d ops/config-snapshots ]; then
    echo "Backing up config snapshots..."
    tar -czf "$BACKUP_DIR/configs_$DATE.tar.gz" ops/config-snapshots/
    echo "✓ Config snapshots backed up"
fi

# 5. Clean old backups (keep last N days)
echo "Cleaning old backups (retention: $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -type f -mtime +$RETENTION_DAYS -delete
echo "✓ Old backups cleaned"

# 6. Upload to S3/cloud (optional, uncomment if configured)
# if command -v aws &> /dev/null; then
#     echo "Uploading to S3..."
#     aws s3 sync "$BACKUP_DIR" "s3://your-bucket/levibot-backups/" --exclude "*" --include "*$DATE*"
#     echo "✓ Uploaded to S3"
# fi

echo ""
echo "✅ Backup complete"
du -sh "$BACKUP_DIR"

