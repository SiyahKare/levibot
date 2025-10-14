#!/bin/bash
# Telethon Quickstart - Interactive setup

set -e

echo "🔥 LeviBot Telegram Integration Quickstart"
echo "==========================================="
echo

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found!"
    echo "Copy ENV.example to .env and configure Telegram variables."
    exit 1
fi

# Check required vars
source .env

if [ -z "$TG_API_ID" ] || [ -z "$TG_API_HASH" ]; then
    echo "❌ TG_API_ID and TG_API_HASH are required!"
    echo
    echo "Get them from: https://my.telegram.org"
    exit 1
fi

echo "✅ Environment configured"
echo

# Check if session exists
SESSION_FILE="backend/data/telethon_session/${TG_SESSION_NAME:-levibot_user}.session"

if [ -f "$SESSION_FILE" ]; then
    echo "✅ Session file found: $SESSION_FILE"
    echo
    echo "🚀 Starting listener in Docker..."
    docker compose up -d --build tg-listener
    echo
    echo "📋 Check logs: docker logs -f levibot-tg-listener"
else
    echo "⚠️  Session file not found: $SESSION_FILE"
    echo
    echo "📱 Running first-time login (interactive)..."
    echo
    python backend/integrations/telethon_listener.py
fi

echo
echo "🎉 Setup complete!"
echo
echo "Next steps:"
echo "  1. View messages: http://localhost:5173 → Integrations"
echo "  2. Score with AI: python backend/feature_store/merge_sentiment.py"
echo "  3. Backfill history: python backend/integrations/telethon_backfill.py @groupname 2000"
echo

