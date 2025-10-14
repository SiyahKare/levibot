#!/bin/bash
# Setup cron jobs for LeviBot monitoring
# Usage: ./scripts/setup_cron.sh [install|remove|status]

PROJECT_ROOT="/Users/onur/levibot"
CRON_SCRIPT="${PROJECT_ROOT}/scripts/health_monitor.sh"
SNAPSHOT_SCRIPT="${PROJECT_ROOT}/scripts/snapshot_flags.py"

ACTION="${1:-install}"

install_cron() {
  echo "🔧 Installing LeviBot cron jobs..."
  
  # Remove existing LeviBot cron jobs
  crontab -l 2>/dev/null | grep -v "levibot" | crontab -
  
  # Add new cron jobs
  (crontab -l 2>/dev/null; echo "# LeviBot Health Monitor - every 5 minutes") | crontab -
  (crontab -l 2>/dev/null; echo "*/5 * * * * bash ${CRON_SCRIPT} >> /tmp/levibot_cron.log 2>&1") | crontab -
  
  (crontab -l 2>/dev/null; echo "# LeviBot Config Snapshot - every 30 minutes") | crontab -
  (crontab -l 2>/dev/null; echo "*/30 * * * * cd ${PROJECT_ROOT} && python3 ${SNAPSHOT_SCRIPT} >> /tmp/levibot_snapshot.log 2>&1") | crontab -
  
  echo "✅ Cron jobs installed:"
  echo "   - Health monitor: every 5 minutes"
  echo "   - Config snapshot: every 30 minutes"
  echo ""
  echo "📁 Logs:"
  echo "   - /tmp/levibot_cron.log"
  echo "   - /tmp/levibot_snapshot.log"
}

remove_cron() {
  echo "🗑️  Removing LeviBot cron jobs..."
  crontab -l 2>/dev/null | grep -v "levibot" | crontab -
  echo "✅ Cron jobs removed"
}

show_status() {
  echo "📊 LeviBot Cron Jobs Status"
  echo "============================"
  echo ""
  
  if crontab -l 2>/dev/null | grep -q "levibot"; then
    echo "✅ Cron jobs installed:"
    crontab -l 2>/dev/null | grep "levibot" -A 1
  else
    echo "❌ No LeviBot cron jobs found"
  fi
  
  echo ""
  echo "📁 Recent logs:"
  if [ -f /tmp/levibot_cron.log ]; then
    echo "Health monitor (last 5 lines):"
    tail -5 /tmp/levibot_cron.log
  else
    echo "No health monitor logs yet"
  fi
}

case "$ACTION" in
  install)
    install_cron
    ;;
  remove)
    remove_cron
    ;;
  status)
    show_status
    ;;
  *)
    echo "Usage: $0 [install|remove|status]"
    echo ""
    echo "Commands:"
    echo "  install - Install cron jobs"
    echo "  remove  - Remove cron jobs"
    echo "  status  - Show cron job status"
    exit 1
    ;;
esac

