# LeviBot ENV Değişkenleri

Aşağıdaki değişkenleri `.env` içine ekleyin (örnek değerler):

```
LEVI_API_BASE=http://127.0.0.1:8000
LEVI_API_HOST=0.0.0.0
LEVI_API_PORT=8000

# Telegram — Bot API (opsiyonel)
LEVI_TELEGRAM_BOT_TOKEN=your_telegram_token_here
LEVI_TELEGRAM_USER_IDS=123456789,987654321
LEVI_DEFAULT_USER_ID=onur

# Telegram — Telethon User-Bot
TELEGRAM_API_ID=123456
TELEGRAM_API_HASH=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TELEGRAM_SESSION_PATH=telegram/sessions/onur.session
# Whitelist / Discovery
TELEGRAM_ALLOWED_CHATS=
TELEGRAM_AUTO_DISCOVER=true
TELEGRAM_ALLOW_PATTERNS=alpha,signal,trade,scalp
TELEGRAM_DENY_PATTERNS=sohbet,chat,random
TELEGRAM_INCLUDE_DM=false
# Backfill
TELEGRAM_STARTUP_HISTORY_LIMIT=200
TELEGRAM_CHECKPOINTS_PATH=telegram/checkpoints.json

# Bybit/Binance API anahtarları (örnek; gerçek değerleri girin)
LEVI_ONUR_BYBIT_KEY=
LEVI_ONUR_BYBIT_SECRET=
LEVI_ONUR_BINANCE_KEY=
LEVI_ONUR_BINANCE_SECRET=

# Opsiyonel: Redis state store
REDIS_URL=redis://localhost:6379/0
```

Notlar:
- Üretimde anahtarları bir gizli kasada tutun (AWS Secrets Manager, Vault, Doppler vb.).
- Testnet için `users.yaml` altında `testnet: true` kullanın.
