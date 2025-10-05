import os


def _b(name: str, default: str = "false") -> bool:
    return os.getenv(name, default).lower() in ("1", "true", "yes", "on")


ALLOWED = [x.strip() for x in os.getenv("TELEGRAM_ALLOWED_CHATS", "").split(",") if x.strip()]
API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
API_HASH = os.getenv("TELEGRAM_API_HASH", "")
SESSION_PATH = os.getenv("TELEGRAM_SESSION_PATH", "telegram/sessions/default.session")

AUTO_DISCOVER = _b("TELEGRAM_AUTO_DISCOVER", "true")
ALLOW_PATTERNS = [x.strip().lower() for x in os.getenv("TELEGRAM_ALLOW_PATTERNS", "").split(",") if x.strip()]
DENY_PATTERNS = [x.strip().lower() for x in os.getenv("TELEGRAM_DENY_PATTERNS", "").split(",") if x.strip()]
INCLUDE_DM = _b("TELEGRAM_INCLUDE_DM", "false")

STARTUP_HISTORY_LIMIT = int(os.getenv("TELEGRAM_STARTUP_HISTORY_LIMIT", "200"))
CHECKPOINTS_PATH = os.getenv("TELEGRAM_CHECKPOINTS_PATH", "telegram/checkpoints.json")


