"""
Token bucket rate limiter.
"""

import time


class TokenBucket:
    """
    Token bucket rate limiter.
    
    Tokens are refilled at a constant rate.
    Burst capacity allows temporary spikes.
    
    Example:
        # 60 requests/minute, burst of 15
        bucket = TokenBucket(rate_per_min=60, burst=15)
        
        if bucket.allow():
            # Make API call
            pass
    """
    
    def __init__(self, rate_per_min: int, burst: int):
        """
        Args:
            rate_per_min: Tokens added per minute
            burst: Maximum bucket capacity
        """
        self.capacity = burst
        self.tokens = float(burst)
        self.rate = rate_per_min / 60.0  # tokens per second
        self.last_update = time.time()
    
    def allow(self) -> bool:
        """
        Check if request is allowed and consume a token.
        
        Returns:
            True if request allowed, False if rate limited
        """
        now = time.time()
        elapsed = now - self.last_update
        
        # Refill tokens based on elapsed time
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.rate
        )
        self.last_update = now
        
        # Check if we have tokens available
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True
        
        return False
    
    def wait_time(self) -> float:
        """
        Get seconds until next token is available.
        
        Returns:
            Seconds to wait (0 if tokens available)
        """
        if self.tokens >= 1.0:
            return 0.0
        
        tokens_needed = 1.0 - self.tokens
        return tokens_needed / self.rate

