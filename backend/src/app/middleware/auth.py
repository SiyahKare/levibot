"""
JWT Authentication & RBAC Middleware
"""
from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

# Environment variables
JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", "24"))

# Security scheme
security = HTTPBearer()


class TokenData(BaseModel):
    """JWT token payload."""

    username: str
    role: str  # admin, trader, viewer
    exp: int


class User(BaseModel):
    """User model for authentication."""

    username: str
    role: str


# Mock user database (replace with real DB later)
MOCK_USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "trader": {"password": "trader123", "role": "trader"},
    "viewer": {"password": "viewer123", "role": "viewer"},
}


def create_access_token(username: str, role: str) -> str:
    """
    Create JWT access token.

    Args:
        username: User identifier
        role: User role (admin/trader/viewer)

    Returns:
        JWT token string
    """
    expire = datetime.now(UTC) + timedelta(hours=JWT_EXPIRY_HOURS)
    payload = {"username": username, "role": role, "exp": int(expire.timestamp())}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> TokenData:
    """
    Decode and validate JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData with username, role, exp

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return TokenData(**payload)
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> User:
    """
    Dependency to extract current user from JWT token.

    Args:
        credentials: HTTP Authorization header with Bearer token

    Returns:
        User object with username and role

    Raises:
        HTTPException: If authentication fails
    """
    token_data = decode_token(credentials.credentials)
    return User(username=token_data.username, role=token_data.role)


async def require_role(required_roles: list[str]):
    """
    Dependency factory to check user role.

    Args:
        required_roles: List of allowed roles (e.g., ["admin", "trader"])

    Returns:
        Dependency function that validates user role
    """

    async def role_checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_roles}",
            )
        return user

    return role_checker


# Pre-defined role dependencies
RequireAdmin = Depends(require_role(["admin"]))
RequireTrader = Depends(require_role(["admin", "trader"]))
RequireViewer = Depends(require_role(["admin", "trader", "viewer"]))


def authenticate_user(username: str, password: str) -> User | None:
    """
    Authenticate user with username and password.

    Args:
        username: User identifier
        password: User password

    Returns:
        User object if authentication succeeds, None otherwise
    """
    if username not in MOCK_USERS:
        return None
    user_data = MOCK_USERS[username]
    if user_data["password"] != password:
        return None
    return User(username=username, role=user_data["role"])

