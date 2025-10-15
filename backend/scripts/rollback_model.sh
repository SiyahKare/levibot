#!/bin/bash
# Rollback model to previous version
#
# Usage:
#   ./scripts/rollback_model.sh 2025-10-14
#   (rolls back to models from 2025-10-14)

set -e

if [ -z "$1" ]; then
  echo "❌ Usage: $0 <date>"
  echo "   Example: $0 2025-10-14"
  exit 1
fi

ROLLBACK_DATE="$1"
MODELS_DIR="backend/data/models"
TARGET_DIR="$MODELS_DIR/$ROLLBACK_DATE"

if [ ! -d "$TARGET_DIR" ]; then
  echo "❌ Model directory not found: $TARGET_DIR"
  echo "Available versions:"
  ls -1 "$MODELS_DIR" | grep -E "^[0-9]{4}-[0-9]{2}-[0-9]{2}$" | sort -r | head -5
  exit 1
fi

echo "🔄 Rolling back to: $ROLLBACK_DATE"
echo "   Target: $TARGET_DIR"

# Backup current symlinks
BACKUP_DIR="$MODELS_DIR/.backup/$(date +%Y-%m-%dT%H-%M-%S)"
mkdir -p "$BACKUP_DIR"

if [ -L "$MODELS_DIR/best_lgbm.pkl" ]; then
  cp -P "$MODELS_DIR/best_lgbm.pkl" "$BACKUP_DIR/"
  echo "   ✅ Backed up: best_lgbm.pkl"
fi

if [ -L "$MODELS_DIR/best_lgbm_model_card.json" ]; then
  cp -P "$MODELS_DIR/best_lgbm_model_card.json" "$BACKUP_DIR/"
  echo "   ✅ Backed up: best_lgbm_model_card.json"
fi

# Update symlinks
ln -sfn "$ROLLBACK_DATE/lgbm.pkl" "$MODELS_DIR/best_lgbm.pkl"
ln -sfn "$ROLLBACK_DATE/model_card.json" "$MODELS_DIR/best_lgbm_model_card.json"

echo "   ✅ Updated: best_lgbm.pkl -> $ROLLBACK_DATE/lgbm.pkl"
echo "   ✅ Updated: best_lgbm_model_card.json -> $ROLLBACK_DATE/model_card.json"

# Verify
if [ -f "$MODELS_DIR/best_lgbm.pkl" ]; then
  echo "✅ Rollback complete!"
  echo "   Current model: $(readlink $MODELS_DIR/best_lgbm.pkl)"
  echo "   Backup saved: $BACKUP_DIR"
else
  echo "❌ Rollback failed: symlink broken"
  exit 1
fi

