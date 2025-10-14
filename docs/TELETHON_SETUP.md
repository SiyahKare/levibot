# Telethon Telegram Integration Setup

## 📋 Overview

LeviBot can ingest live messages from your Telegram groups using a user session (via Telethon). Messages are:

- Streamed to JSONL logs and optionally Redis
- Scored with OpenAI AI Brain for sentiment/impact
- Merged into the feature store for ML models
- Displayed in the panel's Integrations page

---

## 🔑 Prerequisites

### 1. Get Telegram API Credentials

1. Go to [my.telegram.org](https://my.telegram.org)
2. Login with your phone number
3. Navigate to "API development tools"
4. Create a new application
5. Note down your `API_ID` and `API_HASH`

### 2. Configure Environment Variables

Add to your `.env` or `.env.docker`:

```bash
# Telethon User Session
TG_API_ID=123456                     # From my.telegram.org
TG_API_HASH=your_api_hash_here       # From my.telegram.org
TG_PHONE=+1234567890                 # Your phone number (for first login only)
TG_SESSION_NAME=levibot_user         # Session file name
TG_WATCH_LIST=@group1,@group2        # Optional: specific groups (empty = all joined)
REDIS_URL=redis://redis:6379/0       # Optional: Redis streaming (JSONL fallback)
```

---

## 🚀 First-Time Setup (Local)

The first login requires interactive input (SMS code).

### Step 1: Run Listener Locally

```bash
cd /Users/onur/levibot
python backend/integrations/telethon_listener.py
```

### Step 2: Enter Verification Code

You'll be prompted:

```
Enter Telegram code: 12345
```

If 2FA is enabled, you'll also be asked for your password.

### Step 3: Session Saved

Once authenticated, the session file will be saved to:

```
backend/data/telethon_session/levibot_user.session
```

**✅ This file allows headless operation in Docker!**

Press `Ctrl+C` to stop.

---

## 🐳 Running in Docker

After the initial login, the container can run headless:

```bash
# Build and start
docker compose up -d --build tg-listener

# Check logs
docker logs -f levibot-tg-listener

# Stop
docker compose stop tg-listener
```

---

## 📊 Viewing Messages in Panel

1. Open panel: `http://localhost:5173` (or `http://localhost:3001` for Docker)
2. Navigate to **"🔗 Integrations"**
3. See live Telegram messages with AI-scored impact

---

## 🧠 AI Sentiment Scoring

Messages are automatically scored using OpenAI:

```bash
# Run sentiment scoring
python backend/feature_store/merge_sentiment.py
```

This creates `backend/data/sentiment/telegram_impact.parquet` with:

- `ts`: timestamp
- `chat`: group name
- `text`: message text (first 200 chars)
- `impact`: -1 to +1 (bearish to bullish)
- `confidence`: 0 to 1
- `asset`: BTC/ETH/SOL/MKT
- `event_type`: regulation/hack/adoption/etc.

---

## 📜 Message Format (JSONL)

Each message is stored as a JSON line:

```json
{
  "id": 12345,
  "chat": "@crypto_alpha",
  "chat_id": -1001234567890,
  "date": "2025-10-08T10:00:00+00:00",
  "from_id": 987654321,
  "text": "BTC breaking resistance at 65k",
  "reply_to": null,
  "fwd_from": false,
  "urls": ["https://example.com"],
  "edited": false,
  "edit_date": null,
  "media": false,
  "hash": "abc123...",
  "ts_epoch": 1728382800
}
```

---

## 🔍 Backfilling Historical Messages

To fetch past messages from a group:

```bash
python backend/integrations/telethon_backfill.py @groupname 2000
```

This fetches the last 2000 messages and saves them to `backend/data/logs/telethon/backfill.jsonl`.

---

## 🛡️ Security & Privacy

- **User Session**: You're using YOUR Telegram account, not a bot
- **Only Joined Groups**: Can only listen to groups you're already a member of
- **Local Processing**: All data stays on your server
- **No Data Sharing**: Messages are not shared externally
- **Deduplication**: Hash-based to avoid duplicates

---

## 🧷 Troubleshooting

### "FloodWaitError"

Telegram rate-limited you. The listener will automatically wait and retry.

### "PhoneCodeInvalidError"

The SMS code you entered was incorrect. Try again.

### "Session file not found"

Run the first-time setup locally to create the session file.

### Container restarts immediately

Check logs: `docker logs levibot-tg-listener`

Common issues:

- Missing `TG_API_ID` or `TG_API_HASH`
- Session file not mounted (check volumes in `docker-compose.yml`)

---

## 📁 File Structure

```
backend/
├── integrations/
│   ├── telethon_listener.py      # Live message listener
│   ├── telethon_backfill.py      # Historical message fetcher
│   └── __init__.py
├── feature_store/
│   └── merge_sentiment.py        # AI scoring pipeline
└── data/
    ├── telethon_session/
    │   └── levibot_user.session  # Saved auth (auto-created)
    ├── logs/telethon/
    │   ├── stream_*.jsonl        # Live messages
    │   └── backfill.jsonl        # Historical messages
    └── sentiment/
        └── telegram_impact.parquet # AI-scored messages
```

---

## 🔗 Related Documentation

- [AI Brain Guide](./ML_SPRINT1_GUIDE.md) - OpenAI sentiment scoring
- [Feature Store](./ML_SPRINT0_GUIDE.md) - Data pipeline
- [Go-Live Guide](./GO_LIVE_GUIDE.md) - Production deployment

---

## 💡 Tips

1. **Filter Noisy Groups**: Use `TG_WATCH_LIST` to only listen to high-signal groups
2. **Rate Limiting**: Telethon handles this automatically with built-in retry logic
3. **Storage**: Messages are appended to JSONL files - rotate logs periodically
4. **Caching**: OpenAI scores are cached by MD5 hash to avoid re-scoring
5. **Keywords**: Consider adding keyword triggers (e.g., "listing", "hack") for alerts

---

**🎉 You're all set! Messages will stream in real-time and feed your AI models!**
