"""
Authentication Router
Login/logout endpoints for admin access
"""
from typing import Any

from fastapi import APIRouter, Body, Response

from ...infra.audit import audit
from ...infra.auth import sign
from ...infra.settings import settings

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/admin/login")
def admin_login(
    resp: Response,
    key: str = Body(..., embed=True)
) -> dict[str, Any]:
    """
    Admin login with access key.
    
    Args:
        key: Admin access key
    
    Returns:
        Success status and sets HttpOnly cookie
    """
    # Verify admin key
    # If ADMIN_KEY is set, verify it. If not set, allow any key (dev mode)
    if settings.ADMIN_KEY and key != settings.ADMIN_KEY:
        audit("admin_login_failed", {"reason": "invalid_key"})
        return {"ok": False, "error": "Invalid admin key"}
    
    # Generate signed token (24h TTL)
    token = sign("admin", ttl_s=24 * 3600)
    
    # Set HttpOnly cookie
    resp.set_cookie(
        key=settings.ADMIN_COOKIE,
        value=token,
        httponly=True,
        secure=False,  # Set True in production with HTTPS
        samesite="lax",
        max_age=24 * 3600,
        path="/"
    )
    
    audit("admin_login", {"success": True})
    
    return {"ok": True, "message": "Logged in successfully"}


@router.post("/admin/logout")
def admin_logout(resp: Response) -> dict[str, Any]:
    """
    Admin logout.
    
    Clears authentication cookie.
    """
    resp.delete_cookie(key=settings.ADMIN_COOKIE, path="/")
    audit("admin_logout", {})
    return {"ok": True, "message": "Logged out successfully"}


@router.get("/health")
def auth_health() -> dict[str, Any]:
    """Auth service health check."""
    return {
        "ok": True,
        "service": "auth",
        "cookie_name": settings.ADMIN_COOKIE,
        "ip_allowlist_enabled": bool(settings.IP_ALLOWLIST)
    }

