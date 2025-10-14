"""
Simple JSON-based cache with TTL support.
"""

import json
import time
from pathlib import Path
from typing import Any


class JsonCache:
    """
    File-based JSON cache with TTL.
    
    Each key is stored in a separate JSON file.
    Cache entries expire after ttl_seconds.
    """
    
    def __init__(self, base: str = "data/cache", ttl_seconds: int = 3600):
        self.base = Path(base)
        self.base.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl_seconds
    
    def _filepath(self, key: str) -> Path:
        """Convert key to safe filename."""
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.base / f"{safe_key}.json"
    
    def get(self, key: str) -> Any | None:
        """
        Get cached value if not expired.
        
        Returns:
            Cached value if fresh, None if expired or not found
        """
        filepath = self._filepath(key)
        
        if not filepath.exists():
            return None
        
        try:
            data = json.loads(filepath.read_text())
            timestamp = data.get("_ts", 0)
            
            # Check TTL
            if time.time() - timestamp > self.ttl:
                return None
            
            return data.get("value")
        
        except Exception as e:
            print(f"⚠️ Cache read error for {key}: {e}")
            return None
    
    def set(self, key: str, value: Any) -> None:
        """
        Store value in cache with current timestamp.
        """
        filepath = self._filepath(key)
        
        try:
            data = {
                "_ts": time.time(),
                "value": value,
            }
            filepath.write_text(json.dumps(data, indent=2))
        
        except Exception as e:
            print(f"⚠️ Cache write error for {key}: {e}")
    
    def delete(self, key: str) -> None:
        """Delete cache entry."""
        filepath = self._filepath(key)
        if filepath.exists():
            filepath.unlink()
    
    def clear(self) -> None:
        """Clear all cache entries."""
        for filepath in self.base.glob("*.json"):
            filepath.unlink()

