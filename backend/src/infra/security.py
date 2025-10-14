"""
Security Middleware
IP allowlist and admin authentication guards
"""
import hmac

from fastapi import HTTPException, Request

from .auth import verify
from .settings import settings


def ip_allowed(req: Request) -> bool:
    """
    Check if client IP is in allowlist.
    
    Args:
        req: FastAPI request
    
    Returns:
        True if IP is allowed, False otherwise
    """
    if not settings.IP_ALLOWLIST:
        # Empty allowlist = allow all
        return True
    
    client_host = (req.client and req.client.host) or ""
    return client_host in settings.IP_ALLOWLIST


def require_admin(req: Request) -> bool:
    """
    FastAPI dependency for admin authentication.
    
    Checks:
    1. IP allowlist
    2. Cookie auth (HMAC signed token)
    3. Header auth (X-Admin-Key)
    
    Args:
        req: FastAPI request
    
    Returns:
        True if authenticated
    
    Raises:
        HTTPException: 403 if IP not allowed, 401 if not authenticated
    """
    # Check IP allowlist
    if not ip_allowed(req):
        raise HTTPException(status_code=403, detail="IP not allowed")
    
    # Check cookie auth
    token = req.cookies.get(settings.ADMIN_COOKIE)
    if token and verify(token):
        return True
    
    # Check header auth (optional)
    if settings.ADMIN_KEY:
        header_key = req.headers.get("X-Admin-Key", "")
        if hmac_compare(header_key, settings.ADMIN_KEY):
            return True
    
    # No valid auth found
    raise HTTPException(status_code=401, detail="Admin authentication required")


def hmac_compare(a: str, b: str) -> bool:
    """
    Constant-time string comparison.
    
    Args:
        a: First string
        b: Second string
    
    Returns:
        True if strings match
    """
    return hmac.compare_digest(a or "", b or "")
