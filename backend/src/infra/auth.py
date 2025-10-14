"""
Authentication Utilities
HMAC-based cookie signing and verification
"""

import hashlib
import hmac
import time

from .settings import settings


def sign(payload: str, ttl_s: int = 86400) -> str:
    """
    Create signed token with expiration.

    Args:
        payload: Token payload (e.g., "admin")
        ttl_s: Time-to-live in seconds (default: 24h)

    Returns:
        Signed token: payload.expiration.signature
    """
    exp = int(time.time()) + ttl_s
    msg = f"{payload}.{exp}".encode()
    sig = hmac.new(settings.ADMIN_SECRET.encode(), msg, hashlib.sha256).hexdigest()
    return f"{payload}.{exp}.{sig}"


def verify(token: str) -> bool:
    """
    Verify signed token and check expiration.

    Args:
        token: Signed token from cookie

    Returns:
        True if valid and not expired, False otherwise
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return False

        payload, exp, sig = parts

        # Reconstruct message and verify signature
        msg = f"{payload}.{exp}".encode()
        expected_sig = hmac.new(
            settings.ADMIN_SECRET.encode(), msg, hashlib.sha256
        ).hexdigest()

        # Constant-time comparison
        if not hmac.compare_digest(expected_sig, sig):
            return False

        # Check expiration
        return int(exp) >= int(time.time())

    except Exception:
        return False
