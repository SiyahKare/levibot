"""
Authentication router (login, token management).
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..middleware.auth import (
    User,
    authenticate_user,
    create_access_token,
    get_current_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    """Login request body."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response body."""

    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


class UserInfo(BaseModel):
    """User information response."""

    username: str
    role: str
    authenticated: bool = True


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    """
    Authenticate user and return JWT token.

    **Mock credentials (replace with real DB):**
    - admin/admin123 (role: admin)
    - trader/trader123 (role: trader)
    - viewer/viewer123 (role: viewer)

    Args:
        req: Login request with username and password

    Returns:
        JWT access token and user info

    Raises:
        HTTPException: 401 if authentication fails
    """
    user = authenticate_user(req.username, req.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(username=user.username, role=user.role)
    return LoginResponse(
        access_token=token, username=user.username, role=user.role
    )


@router.get("/me", response_model=UserInfo)
async def get_current_user_info(user: Annotated[User, Depends(get_current_user)]):
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.

    Args:
        user: Current user from JWT token (injected by dependency)

    Returns:
        User information (username, role)
    """
    return UserInfo(username=user.username, role=user.role)


@router.post("/logout")
async def logout():
    """
    Logout endpoint (client-side token deletion).

    Note: JWT tokens cannot be invalidated server-side without a blacklist.
    Client should delete the token from storage.

    Returns:
        Success message
    """
    return {"ok": True, "message": "Token should be deleted client-side"}

