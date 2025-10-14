"""
On-chain data fetcher (Dune Analytics, Nansen, etc.).
"""

import random
import time

from ..utils.cache import JsonCache


class OnchainProvider:
    """
    Abstract on-chain data provider interface.
    
    Implementations:
    - Dune Analytics (SQL queries)
    - Nansen API
    - Custom blockchain RPC
    """
    
    async def metrics(self, symbol: str) -> dict[str, float]:
        """
        Fetch on-chain metrics for a symbol.
        
        Returns:
            {
                "active_wallets": 1234,
                "exchange_inflow": 0.5,
                "exchange_outflow": 0.3,
                "funding_rate": 0.01,
                "whale_txs": 10,
                "ts": 1234567890.0,
            }
        """
        raise NotImplementedError


class MockOnchainProvider(OnchainProvider):
    """
    Mock on-chain provider for development/testing.
    
    TODO: Replace with real Dune/Nansen integration in production.
    """
    
    async def metrics(self, symbol: str) -> dict[str, float]:
        """
        Return mock on-chain metrics.
        
        TODO: Implement real queries:
        
        Dune query example:
        ```sql
        SELECT
            COUNT(DISTINCT from_address) as active_wallets,
            SUM(CASE WHEN to_address = 'exchange' THEN value END) as inflow,
            SUM(CASE WHEN from_address = 'exchange' THEN value END) as outflow
        FROM ethereum.transactions
        WHERE block_time > NOW() - INTERVAL '1 hour'
        AND token = 'BTC'
        ```
        """
        return {
            "active_wallets": float(random.randint(1000, 5000)),
            "exchange_inflow": random.uniform(0.0, 1.0),
            "exchange_outflow": random.uniform(0.0, 1.0),
            "funding_rate": random.uniform(-0.05, 0.05),
            "whale_txs": float(random.randint(0, 20)),
            "ts": time.time(),
        }


class DuneOnchainProvider(OnchainProvider):
    """
    Dune Analytics on-chain provider.
    
    TODO: Implement
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def metrics(self, symbol: str) -> dict[str, float]:
        """
        Execute Dune query and parse results.
        
        TODO: Implement
        """
        # Example:
        # response = await httpx.post(
        #     f"https://api.dune.com/api/v1/query/{query_id}/execute",
        #     headers={"X-Dune-API-Key": self.api_key},
        #     json={"query_parameters": {"symbol": symbol}}
        # )
        # return response.json()["result"]["rows"][0]
        raise NotImplementedError


class OnchainFetcher:
    """
    High-level on-chain data fetcher with caching.
    """
    
    def __init__(self, provider: OnchainProvider, ttl_seconds: int = 300):
        """
        Args:
            provider: On-chain data provider
            ttl_seconds: Cache TTL (default 5 minutes)
        """
        self.provider = provider
        self.cache = JsonCache(base="data/cache/onchain", ttl_seconds=ttl_seconds)
    
    async def get_metrics(self, symbol: str) -> dict[str, float]:
        """
        Get on-chain metrics for a symbol.
        
        Results are cached for ttl_seconds.
        
        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
        
        Returns:
            On-chain metrics dictionary
        """
        cache_key = f"onchain:{symbol}"
        
        # Check cache
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Fetch fresh data
        data = await self.provider.metrics(symbol)
        
        # Cache result
        self.cache.set(cache_key, data)
        
        return data

