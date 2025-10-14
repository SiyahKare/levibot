#!/bin/bash
# LeviBot Database Backup
# Daily backup with 14-day retention
# Usage: ./scripts/db_backup.sh [manual|auto]

BACKUP_DIR="/Users/onur/levibot/backups/db"
RETENTION_DAYS=14
TIMESTAMP=$(date '+%Y-%m-%d_%H%M%S')
BACKUP_FILE="${BACKUP_DIR}/levibot_${TIMESTAMP}.sql.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo "🗄️  LeviBot Database Backup"
echo "=========================="
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Backup database
echo "📦 Backing up database..."
if docker exec levibot-timescaledb pg_dump -U postgres levibot | gzip > "$BACKUP_FILE"; then
  SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
  echo "✅ Backup successful: $BACKUP_FILE ($SIZE)"
else
  echo "❌ Backup failed!"
  exit 1
fi

# Cleanup old backups
echo ""
echo "🧹 Cleaning up old backups (older than ${RETENTION_DAYS} days)..."
find "$BACKUP_DIR" -name "levibot_*.sql.gz" -type f -mtime +${RETENTION_DAYS} -delete
REMAINING=$(ls -1 "$BACKUP_DIR" | wc -l)
echo "✅ Cleanup complete. Backups remaining: $REMAINING"

# Summary
echo ""
echo "📊 Recent Backups:"
ls -lht "$BACKUP_DIR" | head -6

exit 0

