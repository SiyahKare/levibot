#!/usr/bin/env bash
# Setup Cron Jobs for ML Monitoring

cat << 'EOF'
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🕐 ML MONITORING CRON SETUP
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Add these to your crontab (crontab -e):

# Drift detection every 15 minutes
*/15 * * * * cd /Users/onur/levibot && python backend/scripts/drift_check.py >> /tmp/drift_check.log 2>&1

# Ensemble weight tuning every hour
0 * * * * cd /Users/onur/levibot && python backend/scripts/ensemble_tuner.py >> /tmp/ensemble_tuner.log 2>&1

# Model retraining weekly (Sunday 2 AM)
0 2 * * 0 cd /Users/onur/levibot && python backend/scripts/train_ml_model.py --symbol BTCUSDT --days 45 >> /tmp/retrain.log 2>&1

# Feature data refresh daily (every 6 hours)
0 */6 * * * cd /Users/onur/levibot && python backend/ml/feature_store/ingest_multi.py >> /tmp/ingest.log 2>&1

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

To install:
  ./backend/scripts/cron_setup.sh >> /tmp/levibot_cron.txt
  crontab /tmp/levibot_cron.txt

To verify:
  crontab -l

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EOF

