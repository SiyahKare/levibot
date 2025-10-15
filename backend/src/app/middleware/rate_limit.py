"""
Rate Limiting Middleware (Token Bucket Algorithm)
"""
from __future__ import annotations

import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, Request, status


class TokenBucket:
    """
    Token bucket rate limiter.

    Attributes:
        capacity: Maximum number of tokens
        refill_rate: Tokens per second
        tokens: Current token count
        last_refill: Last refill timestamp
    """

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()

    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens consumed, False if rate limit exceeded
        """
        now = time.time()
        elapsed = now - self.last_refill

        # Refill tokens based on elapsed time
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimiter:
    """
    Rate limiter using token bucket algorithm.

    Buckets are keyed by (user, IP, endpoint).
    """

    def __init__(self, requests_per_minute: int = 60):
        self.rpm = requests_per_minute
        self.capacity = requests_per_minute
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        self.buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(self.capacity, self.refill_rate)
        )

    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed.

        Args:
            key: Rate limit key (e.g., "user@ip:endpoint")

        Returns:
            True if allowed, False if rate limited
        """
        return self.buckets[key].consume(1)


# Global rate limiter instance
_rate_limiter = RateLimiter(requests_per_minute=60)


async def rate_limit_middleware(request: Request) -> None:
    """
    Rate limiting middleware for FastAPI.

    Args:
        request: FastAPI request object

    Raises:
        HTTPException: 429 Too Many Requests if rate limit exceeded
    """
    # Extract user from JWT (if authenticated)
    user = "anonymous"
    if "authorization" in request.headers:
        # Parse username from JWT (simple extraction, not validated here)
        try:
            token = request.headers["authorization"].split(" ")[1]
            # Note: This is simplified; in production, decode properly
            user = token[:10]  # Use first 10 chars as identifier
        except Exception:
            pass

    # Extract IP
    client_ip = request.client.host if request.client else "unknown"

    # Extract endpoint
    endpoint = request.url.path

    # Create rate limit key
    key = f"{user}@{client_ip}:{endpoint}"

    # Check rate limit
    if not _rate_limiter.is_allowed(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded: {_rate_limiter.rpm} requests per minute",
            headers={"Retry-After": "60"},
        )

