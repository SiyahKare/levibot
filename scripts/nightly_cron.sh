#!/usr/bin/env bash
#
# Nightly AutoML runner script
# Runs data collection → feature engineering → training → deployment
#

set -e

# Change to repo root
cd "$(dirname "$0")/.."

# Set Python path
export PYTHONPATH=.

# Set symbols (override with env var if needed)
export SYMBOLS="${SYMBOLS:-BTCUSDT,ETHUSDT,SOLUSDT,ATOMUSDT,AVAXUSDT}"

# Log start
echo "=========================================="
echo "🌙 Nightly AutoML — $(date)"
echo "=========================================="

# Run nightly retrain
python -m backend.src.automl.nightly_retrain

# Log completion
echo "=========================================="
echo "✅ Nightly AutoML Complete — $(date)"
echo "=========================================="

