#!/bin/bash
# Setup log rotation for LeviBot
# Usage: ./scripts/setup_logrotate.sh [install|remove]

LOGROTATE_CONF="/etc/logrotate.d/levibot"
ACTION="${1:-install}"

install_logrotate() {
  echo "📋 Installing log rotation config..."
  
  sudo tee "$LOGROTATE_CONF" > /dev/null <<'EOF'
# LeviBot log rotation
/tmp/levibot*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
    copytruncate
    dateext
    dateformat -%Y%m%d
}

/Users/onur/levibot/backend/data/logs/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
    copytruncate
    dateext
    dateformat -%Y%m%d
}

/Users/onur/levibot/ops/audit.log {
    daily
    rotate 90
    compress
    missingok
    notifempty
    copytruncate
    dateext
    dateformat -%Y%m%d
}
EOF

  echo "✅ Logrotate config installed: $LOGROTATE_CONF"
  echo ""
  echo "Test config:"
  sudo logrotate -d "$LOGROTATE_CONF" 2>&1 | head -20
}

remove_logrotate() {
  echo "🗑️  Removing log rotation config..."
  sudo rm -f "$LOGROTATE_CONF"
  echo "✅ Logrotate config removed"
}

case "$ACTION" in
  install)
    install_logrotate
    ;;
  remove)
    remove_logrotate
    ;;
  *)
    echo "Usage: $0 [install|remove]"
    exit 1
    ;;
esac

