"""
Recovery policy for crashed engines.
"""

import time


class RecoveryPolicy:
    """
    Determines recovery behavior for crashed engines.
    
    Rules:
    - Max 5 restarts per engine per hour
    - Exponential backoff between restarts
    """
    
    def __init__(
        self,
        max_restarts_per_hour: int = 5,
        backoff_base: int = 60,
    ):
        self.max_restarts_per_hour = max_restarts_per_hour
        self.backoff_base = backoff_base
        
        # Track restart attempts: {symbol: [timestamp, timestamp, ...]}
        self.restart_history: dict[str, list[float]] = {}
    
    def should_recover(self, symbol: str) -> bool:
        """
        Check if engine should be recovered.
        
        Returns:
            bool: True if recovery allowed, False otherwise
        """
        now = time.time()
        one_hour_ago = now - 3600
        
        # Get restart history for this symbol
        if symbol not in self.restart_history:
            self.restart_history[symbol] = []
        
        # Filter out old restarts (> 1 hour ago)
        recent_restarts = [
            ts for ts in self.restart_history[symbol]
            if ts > one_hour_ago
        ]
        self.restart_history[symbol] = recent_restarts
        
        # Check restart limit
        if len(recent_restarts) >= self.max_restarts_per_hour:
            print(f"❌ Max restarts ({self.max_restarts_per_hour}/hour) reached for {symbol}")
            return False
        
        # Check exponential backoff
        if recent_restarts:
            last_restart = recent_restarts[-1]
            attempts = len(recent_restarts)
            min_wait = self.backoff_base * (2 ** (attempts - 1))
            
            elapsed = now - last_restart
            if elapsed < min_wait:
                print(f"⏳ Backoff active for {symbol}: {int(min_wait - elapsed)}s remaining")
                return False
        
        # Record this restart
        self.restart_history[symbol].append(now)
        return True
    
    def reset(self, symbol: str) -> None:
        """Reset restart history for a symbol."""
        if symbol in self.restart_history:
            del self.restart_history[symbol]
    
    def get_stats(self, symbol: str) -> dict[str, any]:
        """Get restart statistics for a symbol."""
        now = time.time()
        one_hour_ago = now - 3600
        
        history = self.restart_history.get(symbol, [])
        recent = [ts for ts in history if ts > one_hour_ago]
        
        return {
            "symbol": symbol,
            "restarts_last_hour": len(recent),
            "max_restarts_per_hour": self.max_restarts_per_hour,
            "last_restart": recent[-1] if recent else None,
        }

