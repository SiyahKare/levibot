"""
Audit logging middleware.

Logs all API requests/responses with user, role, IP, action, and outcome.
"""
from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class AuditLogMiddleware(BaseHTTPMiddleware):
    """
    Audit log middleware for FastAPI.

    Logs:
    - Timestamp (UTC)
    - User (from JWT if available)
    - Role (from JWT if available)
    - IP address
    - Method + Path
    - Status code
    - Duration (ms)
    - Request body (for sensitive endpoints)
    """

    def __init__(self, app, log_dir: str = "backend/data/audit"):
        super().__init__(app)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Sensitive endpoints to log request body
        self.sensitive_paths = {
            "/auth/login",
            "/live/kill",
            "/live/restore",
            "/engines/stop",
            "/engines/start",
        }

    async def dispatch(self, request: Request, call_next):
        """Process request and log audit trail."""
        start_time = time.time()

        # Extract user info (if JWT present)
        user = getattr(request.state, "user", None)
        username = user.get("username") if user else "anonymous"
        role = user.get("role") if user else "guest"

        # Client IP
        client_ip = request.client.host if request.client else "unknown"

        # Request body (for sensitive endpoints)
        request_body = None
        if request.url.path in self.sensitive_paths:
            try:
                body_bytes = await request.body()
                request_body = body_bytes.decode("utf-8") if body_bytes else None
            except Exception:
                request_body = "<error reading body>"

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        # Build audit log entry
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "user": username,
            "role": role,
            "ip": client_ip,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params) if request.query_params else None,
            "status": response.status_code,
            "duration_ms": round(duration_ms, 2),
        }

        # Add request body for sensitive endpoints
        if request_body:
            log_entry["request_body"] = request_body

        # Write to daily log file
        self._write_log(log_entry)

        return response

    def _write_log(self, entry: dict):
        """Write log entry to daily JSONL file."""
        try:
            # Daily log file
            log_file = self.log_dir / f"{datetime.now(UTC).strftime('%Y-%m-%d')}.jsonl"

            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")

        except Exception as e:
            # Don't fail request if logging fails
            print(f"⚠️ Audit log write failed: {e}")


def get_audit_logs(date: str | None = None, limit: int = 100) -> list[dict]:
    """
    Read audit logs for a given date.

    Args:
        date: Date string (YYYY-MM-DD), defaults to today
        limit: Max number of entries to return

    Returns:
        List of audit log entries
    """
    if date is None:
        date = datetime.now(UTC).strftime("%Y-%m-%d")

    log_file = Path("backend/data/audit") / f"{date}.jsonl"

    if not log_file.exists():
        return []

    entries = []
    with open(log_file) as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                entries.append(entry)
            except json.JSONDecodeError:
                continue

    # Return last N entries
    return entries[-limit:]

