#!/bin/bash
# Rollback model to previous version (supports LGBM + TFT)
#
# Usage:
#   ./scripts/rollback_model.sh 2025-10-14 [lgbm|tft|all]
#   ./scripts/rollback_model.sh list

set -e

MODELS_DIR="backend/data/models"

# List available versions
if [ "$1" = "list" ] || [ -z "$1" ]; then
  echo "📦 Available model versions:"
  for dir in "$MODELS_DIR"/*/; do
    if [ -d "$dir" ]; then
      version=$(basename "$dir")
      models=""
      [ -f "$dir/lgbm.pkl" ] && models="$models LGBM"
      [ -f "$dir/tft.pt" ] && models="$models TFT"
      [ -n "$models" ] && echo "   ✓ $version [$models]"
    fi
  done
  exit 0
fi

ROLLBACK_DATE="$1"
MODEL_TYPE="${2:-all}"  # lgbm, tft, or all
TARGET_DIR="$MODELS_DIR/$ROLLBACK_DATE"

if [ ! -d "$TARGET_DIR" ]; then
  echo "❌ Model directory not found: $TARGET_DIR"
  echo "Run './scripts/rollback_model.sh list' to see available versions."
  exit 1
fi

echo "🔄 Rolling back to: $ROLLBACK_DATE (type: $MODEL_TYPE)"

# Backup current symlinks
BACKUP_DIR="$MODELS_DIR/.backup/$(date +%Y-%m-%dT%H-%M-%S)"
mkdir -p "$BACKUP_DIR"

# Rollback LGBM
rollback_lgbm() {
  if [ -L "$MODELS_DIR/best_lgbm.pkl" ]; then
    cp -P "$MODELS_DIR/best_lgbm.pkl" "$BACKUP_DIR/"
  fi
  if [ -L "$MODELS_DIR/best_lgbm_model_card.json" ]; then
    cp -P "$MODELS_DIR/best_lgbm_model_card.json" "$BACKUP_DIR/"
  fi
  
  ln -sfn "$ROLLBACK_DATE/lgbm.pkl" "$MODELS_DIR/best_lgbm.pkl"
  ln -sfn "$ROLLBACK_DATE/model_card.json" "$MODELS_DIR/best_lgbm_model_card.json"
  
  echo "   ✅ LGBM rolled back"
}

# Rollback TFT
rollback_tft() {
  if [ -L "$MODELS_DIR/best_tft.pt" ]; then
    cp -P "$MODELS_DIR/best_tft.pt" "$BACKUP_DIR/"
  fi
  if [ -L "$MODELS_DIR/best_tft_model_card.json" ]; then
    cp -P "$MODELS_DIR/best_tft_model_card.json" "$BACKUP_DIR/"
  fi
  
  ln -sfn "$ROLLBACK_DATE/tft.pt" "$MODELS_DIR/best_tft.pt"
  ln -sfn "$ROLLBACK_DATE/tft_model_card.json" "$MODELS_DIR/best_tft_model_card.json"
  
  echo "   ✅ TFT rolled back"
}

# Execute rollback
case "$MODEL_TYPE" in
  lgbm) rollback_lgbm ;;
  tft) rollback_tft ;;
  all) rollback_lgbm; rollback_tft ;;
  *) echo "❌ Invalid type: $MODEL_TYPE (use lgbm, tft, or all)"; exit 1 ;;
esac

echo "✅ Rollback complete! Backup: $BACKUP_DIR"

