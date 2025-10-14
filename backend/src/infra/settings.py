"""
Centralized Settings for LEVIBOT Realtime
"""

from __future__ import annotations

import os
from pathlib import Path


class Settings:
    """Global configuration loaded from environment."""

    # --- Core ---
    ENV = os.getenv("ENV", "dev")
    PAPER = os.getenv("PAPER", "true").lower() == "true"
    EXCHANGE = os.getenv("EXCHANGE", "MEXC")

    # --- Database ---
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    PG_DSN = os.getenv("PG_DSN", "")  # postgresql://user:pass@host:5432/levibot

    # TimescaleDB connection (for direct queries, feature loading)
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "5432"))
    DB_NAME = os.getenv("DB_NAME", "levibot")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")

    # --- AI/Telegram ---
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_ALERT_CHAT_ID = os.getenv("TELEGRAM_ALERT_CHAT_ID", "")
    TELETHON_API_ID = int(os.getenv("TELETHON_API_ID", "0"))
    TELETHON_API_HASH = os.getenv("TELETHON_API_HASH", "")
    TELETHON_SESSION = os.getenv("TELETHON_SESSION", "levibot.session")

    # --- AI Reason (Trade Explanations) ---
    AI_REASON_ENABLED = bool(int(os.getenv("AI_REASON_ENABLED", "1")))
    AI_REASON_TIMEOUT_S = float(os.getenv("AI_REASON_TIMEOUT_S", "1.2"))
    AI_REASON_MONTHLY_TOKEN_BUDGET = int(
        os.getenv("AI_REASON_MONTHLY_TOKEN_BUDGET", "250000")
    )  # ~250k tokens/month

    # --- Trading ---
    SYMBOLS = [s.strip() for s in os.getenv("SYMBOLS", "BTCUSDT,ETHUSDT").split(",")]
    SLIPPAGE_BPS = float(os.getenv("SLIPPAGE_BPS", "2.0"))
    FEE_TAKER_BPS = float(os.getenv("FEE_TAKER_BPS", "5.0"))
    FEE_MAKER_BPS = float(os.getenv("FEE_MAKER_BPS", "2.0"))
    MAX_DAILY_LOSS = float(os.getenv("MAX_DAILY_LOSS", "-200.0"))
    MAX_POS_NOTIONAL = float(os.getenv("MAX_POS_NOTIONAL", "2000.0"))

    # --- WebSocket ---
    WS_RECONNECT_SECS = int(os.getenv("WS_RECONNECT_SECS", "3"))
    WS_PING_INTERVAL = int(os.getenv("WS_PING_INTERVAL", "20"))

    # --- Redis Streams ---
    STREAM_TOPIC_TICKS = os.getenv("STREAM_TOPIC_TICKS", "ticks")
    STREAM_TOPIC_SIGNALS = os.getenv("STREAM_TOPIC_SIGNALS", "signals")
    STREAM_TOPIC_EVENTS = os.getenv("STREAM_TOPIC_EVENTS", "events")
    STREAM_MAXLEN = int(os.getenv("STREAM_MAXLEN", "10000"))

    # --- Data Persistence ---
    DATA_DIR = os.getenv(
        "DATA_DIR", str(Path(__file__).resolve().parents[3] / "backend" / "data")
    )
    LOG_DIR = os.getenv("LOG_DIR", "")  # Empty means auto-detect

    # --- MEXC API (Optional for REST fallback) ---
    MEXC_API_KEY = os.getenv("MEXC_API_KEY", "")
    MEXC_API_SECRET = os.getenv("MEXC_API_SECRET", "")
    MEXC_SANDBOX = os.getenv("MEXC_SANDBOX", "false").lower() == "true"

    # --- Performance ---
    DB_BATCH_SIZE = int(os.getenv("DB_BATCH_SIZE", "500"))
    DB_FLUSH_INTERVAL_SEC = float(os.getenv("DB_FLUSH_INTERVAL_SEC", "0.25"))

    # --- Security & Rate Limiting ---
    OPENAI_RPM = int(os.getenv("OPENAI_RPM", "60"))  # Requests per minute
    TELEGRAM_RPS = float(os.getenv("TELEGRAM_RPS", "1.0"))  # Requests per second
    ALLOW_IPS = [
        ip.strip() for ip in os.getenv("ALLOW_IPS", "").split(",") if ip.strip()
    ]
    MASK_SECRETS_IN_LOGS = os.getenv("MASK_SECRETS_IN_LOGS", "true").lower() == "true"
    API_RATE_LIMIT_PER_MINUTE = int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "100"))

    # --- Admin Authentication ---
    ADMIN_SECRET = os.getenv("ADMIN_SECRET", "dev-secret-change-me")  # HMAC signing key
    ADMIN_KEY = os.getenv("ADMIN_KEY", "")  # Admin access key
    ADMIN_COOKIE = os.getenv("ADMIN_COOKIE", "adm")  # Cookie name
    IP_ALLOWLIST = [
        ip.strip()
        for ip in os.getenv("IP_ALLOWLIST", "127.0.0.1,::1").split(",")
        if ip.strip()
    ]

    # --- Monitoring ---
    SENTRY_DSN = os.getenv("SENTRY_DSN", "")
    SENTRY_ENABLED = os.getenv("SENTRY_ENABLED", "false").lower() == "true"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
