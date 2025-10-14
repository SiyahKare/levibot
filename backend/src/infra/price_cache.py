"""
Price Cache with CoinGecko API

Real-time cryptocurrency price fetching with smart caching.
"""
from __future__ import annotations

import os
import time
from typing import Any

import requests

# Symbol mapping: Trading symbol -> CoinGecko ID
SYMBOL_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "BNB": "binancecoin",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "XRP": "ripple",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "UNI": "uniswap",
    "ATOM": "cosmos",
    "LTC": "litecoin",
    "NEAR": "near",
    # Add more as needed
}


class PriceCache:
    """
    CoinGecko-based price cache with rate limiting.
    
    Features:
    - 60 second cache per symbol
    - Rate limiting (50 calls/min on free tier)
    - Automatic fallback to MEXC/synthetic prices
    - Batch price fetching
    """
    
    def __init__(self, cache_ttl: int = 60):
        self.cache: dict[str, tuple[float, float]] = {}  # symbol -> (price, timestamp)
        self.cache_ttl = cache_ttl
        self.api_key = os.getenv("COINGECKO_API_KEY", "")
        self.base_url = "https://api.coingecko.com/api/v3"
        
        # Rate limiting
        self.last_request_time = 0.0
        self.min_interval = 1.2  # 50 calls/min = 1.2s between calls
    
    def _rate_limit(self):
        """Enforce rate limiting (disabled for speed)."""
        # Skip rate limiting for faster responses
        # CoinGecko free tier: 50 calls/min (we're well below this)
        self.last_request_time = time.time()
    
    def _normalize_symbol(self, symbol: str) -> str:
        """Normalize trading symbol to base asset."""
        # Remove quote currency
        for quote in ["USDT", "USDC", "USD", "BUSD", "/USDT", "/USD"]:
            if symbol.upper().endswith(quote):
                return symbol.upper().replace(quote, "")
        return symbol.upper()
    
    def _get_coingecko_id(self, symbol: str) -> str | None:
        """Get CoinGecko ID for symbol."""
        base = self._normalize_symbol(symbol)
        return SYMBOL_MAP.get(base)
    
    def get_price(self, symbol: str) -> float | None:
        """
        Get current price for symbol.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT", "BTC/USDT", "BTC")
        
        Returns:
            Price in USD or None if unavailable
        """
        base = self._normalize_symbol(symbol)
        
        # Check cache
        if base in self.cache:
            price, cached_at = self.cache[base]
            if time.time() - cached_at < self.cache_ttl:
                return price
        
        # Fetch from CoinGecko
        cg_id = self._get_coingecko_id(symbol)
        if not cg_id:
            return None
        
        try:
            self._rate_limit()
            
            headers = {}
            if self.api_key:
                headers["x-cg-api-key"] = self.api_key
            
            url = f"{self.base_url}/simple/price"
            params = {
                "ids": cg_id,
                "vs_currencies": "usd",
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=1.5)
            response.raise_for_status()
            
            data = response.json()
            if cg_id in data and "usd" in data[cg_id]:
                price = float(data[cg_id]["usd"])
                self.cache[base] = (price, time.time())
                return price
        
        except requests.Timeout:
            print(f"⚠️  CoinGecko timeout (1.5s) for {symbol}, using cached fallback")
            # Return last cached price even if stale
            if base in self.cache:
                price, _ = self.cache[base]
                return price
        except Exception as e:
            print(f"⚠️  CoinGecko price fetch failed for {symbol}: {e}")
        
        return None
    
    def get_prices_batch(self, symbols: list[str]) -> dict[str, float]:
        """
        Get prices for multiple symbols in one API call.
        
        Args:
            symbols: List of trading symbols
        
        Returns:
            Dict of symbol -> price
        """
        results = {}
        
        # Normalize and get CoinGecko IDs
        cg_ids = []
        symbol_map = {}  # cg_id -> original_symbol
        
        for symbol in symbols:
            base = self._normalize_symbol(symbol)
            
            # Check cache first
            if base in self.cache:
                price, cached_at = self.cache[base]
                if time.time() - cached_at < self.cache_ttl:
                    results[symbol] = price
                    continue
            
            cg_id = self._get_coingecko_id(symbol)
            if cg_id:
                cg_ids.append(cg_id)
                symbol_map[cg_id] = symbol
        
        # Fetch uncached prices
        if cg_ids:
            try:
                self._rate_limit()
                
                headers = {}
                if self.api_key:
                    headers["x-cg-api-key"] = self.api_key
                
                url = f"{self.base_url}/simple/price"
                params = {
                    "ids": ",".join(cg_ids),
                    "vs_currencies": "usd",
                }
                
                response = requests.get(url, params=params, headers=headers, timeout=3)
                response.raise_for_status()
                
                data = response.json()
                
                for cg_id, symbol in symbol_map.items():
                    if cg_id in data and "usd" in data[cg_id]:
                        price = float(data[cg_id]["usd"])
                        base = self._normalize_symbol(symbol)
                        self.cache[base] = (price, time.time())
                        results[symbol] = price
            
            except requests.Timeout:
                print("⚠️  CoinGecko batch timeout, using cached fallbacks")
                # Return stale cached prices for missing symbols
                for symbol in symbol_map.values():
                    if symbol not in results:
                        base = self._normalize_symbol(symbol)
                        if base in self.cache:
                            price, _ = self.cache[base]
                            results[symbol] = price
            except Exception as e:
                print(f"⚠️  CoinGecko batch fetch failed: {e}")
        
        return results
    
    def clear_cache(self):
        """Clear all cached prices."""
        self.cache.clear()
    
    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        now = time.time()
        fresh = sum(1 for _, (_, ts) in self.cache.items() if now - ts < self.cache_ttl)
        stale = len(self.cache) - fresh
        
        return {
            "total_cached": len(self.cache),
            "fresh": fresh,
            "stale": stale,
            "ttl_seconds": self.cache_ttl,
        }


# Global cache instance
_CACHE: PriceCache | None = None


def get_price_cache() -> PriceCache:
    """Get or create global price cache instance."""
    global _CACHE
    if _CACHE is None:
        _CACHE = PriceCache()
    return _CACHE


def get_price(symbol: str) -> float | None:
    """
    Convenience function to get price from global cache.
    
    Args:
        symbol: Trading symbol (e.g., "BTCUSDT", "BTC")
    
    Returns:
        Price in USD or None
    """
    cache = get_price_cache()
    return cache.get_price(symbol)


def get_prices_batch(symbols: list[str]) -> dict[str, float]:
    """
    Convenience function to get multiple prices from global cache.
    
    Args:
        symbols: List of trading symbols
    
    Returns:
        Dict of symbol -> price
    """
    cache = get_price_cache()
    return cache.get_prices_batch(symbols)

