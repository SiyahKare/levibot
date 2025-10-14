"""
Audit Logging
Records admin actions for security compliance
"""

import json
import os
import time
from pathlib import Path
from typing import Any

# Audit log path
LOG_PATH = os.getenv("AUDIT_LOG", "ops/audit.log")

# Ensure directory exists
Path(LOG_PATH).parent.mkdir(parents=True, exist_ok=True)


def audit(event: str, meta: dict[str, Any]) -> None:
    """
    Log admin action to audit log.

    Args:
        event: Event type (e.g., "canary", "kill", "flags_update")
        meta: Additional metadata (e.g., {"ip": "127.0.0.1", "state": "on"})

    Format:
        JSON line: {"ts": 1234567890.123, "event": "canary", "ip": "127.0.0.1", ...}
    """
    try:
        record = {"ts": time.time(), "event": event, **meta}

        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(record) + "\n")

    except Exception as e:
        # Log error but don't fail the request
        print(f"⚠️  Audit logging failed: {e}")
