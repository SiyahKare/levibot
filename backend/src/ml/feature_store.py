"""
Feature Store - Hot cache + historical feature lookup
Optimized for low-latency ML inference and backtesting
"""

import json
import time
from dataclasses import asdict, dataclass

import numpy as np
import redis.asyncio as aioredis


@dataclass
class FeatureVector:
    """Feature vector for ML model"""

    symbol: str
    timestamp: float

    # Price features
    price: float
    vwap_dev: float
    zscore: float
    atr: float
    rsi: float

    # Volume features
    vol_ratio: float
    vol_imbalance: float

    # Microstructure
    spread_bps: float
    ofi: float  # Order flow imbalance proxy

    # Regime
    regime: int  # 0=ranging, 1=trending, 2=volatile
    volatility_regime: int  # 0=low, 1=medium, 2=high

    def to_array(self) -> np.ndarray:
        """Convert to numpy array for model input"""
        return np.array(
            [
                self.vwap_dev,
                self.zscore,
                self.atr,
                self.rsi,
                self.vol_ratio,
                self.vol_imbalance,
                self.spread_bps,
                self.ofi,
                float(self.regime),
                float(self.volatility_regime),
            ]
        )

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FeatureVector":
        return cls(**data)


class FeatureStore:
    """
    Feature store with hot cache and historical lookup

    Architecture:
    - Redis: Hot cache (last 1000 ticks per symbol)
    - ClickHouse: Historical features (90 days)
    - In-memory: Real-time feature calculation buffer
    """

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self._client: aioredis.Redis | None = None
        self._buffer: dict[str, list[FeatureVector]] = {}
        self._buffer_size = 100

    async def connect(self):
        """Initialize Redis connection"""
        if self._client is None:
            self._client = await aioredis.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )

    async def disconnect(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None

    async def store_features(self, symbol: str, features: FeatureVector):
        """
        Store feature vector in hot cache

        Args:
            symbol: Trading symbol
            features: Feature vector
        """
        await self.connect()

        key = f"features:{symbol}"

        # Store in Redis sorted set (sorted by timestamp)
        await self._client.zadd(
            key, {json.dumps(features.to_dict()): features.timestamp}
        )

        # Keep only last 1000 entries
        await self._client.zremrangebyrank(key, 0, -1001)

        # Also buffer in memory for ultra-fast access
        if symbol not in self._buffer:
            self._buffer[symbol] = []

        self._buffer[symbol].append(features)

        # Keep buffer size limited
        if len(self._buffer[symbol]) > self._buffer_size:
            self._buffer[symbol] = self._buffer[symbol][-self._buffer_size :]

    async def get_latest_features(self, symbol: str) -> FeatureVector | None:
        """
        Get latest feature vector for symbol

        Args:
            symbol: Trading symbol

        Returns:
            Latest FeatureVector or None
        """
        # Try memory buffer first (fastest)
        if symbol in self._buffer and self._buffer[symbol]:
            return self._buffer[symbol][-1]

        # Fallback to Redis
        await self.connect()
        key = f"features:{symbol}"

        result = await self._client.zrevrange(key, 0, 0)
        if not result:
            return None

        data = json.loads(result[0])
        return FeatureVector.from_dict(data)

    async def get_features_window(
        self, symbol: str, window_size: int = 20
    ) -> list[FeatureVector]:
        """
        Get recent feature vectors (for sequence models)

        Args:
            symbol: Trading symbol
            window_size: Number of recent vectors

        Returns:
            List of FeatureVectors
        """
        # Try memory buffer first
        if symbol in self._buffer and len(self._buffer[symbol]) >= window_size:
            return self._buffer[symbol][-window_size:]

        # Fallback to Redis
        await self.connect()
        key = f"features:{symbol}"

        results = await self._client.zrevrange(key, 0, window_size - 1)
        if not results:
            return []

        features = [FeatureVector.from_dict(json.loads(r)) for r in reversed(results)]

        return features

    async def get_features_array(
        self, symbol: str, window_size: int = 20
    ) -> np.ndarray:
        """
        Get feature window as numpy array (ready for model input)

        Returns:
            Array of shape (window_size, num_features)
        """
        features = await self.get_features_window(symbol, window_size)

        if not features:
            return np.array([])

        return np.array([f.to_array() for f in features])

    async def compute_rolling_stats(self, symbol: str, window: int = 20) -> dict:
        """
        Compute rolling statistics for features

        Returns:
            Dict with mean, std, min, max for each feature
        """
        arr = await self.get_features_array(symbol, window)

        if arr.size == 0:
            return {}

        return {
            "mean": arr.mean(axis=0).tolist(),
            "std": arr.std(axis=0).tolist(),
            "min": arr.min(axis=0).tolist(),
            "max": arr.max(axis=0).tolist(),
        }

    async def get_feature_freshness(self, symbol: str) -> float | None:
        """
        Get age of latest features in seconds

        Returns:
            Age in seconds or None if no features
        """
        latest = await self.get_latest_features(symbol)

        if latest is None:
            return None

        return time.time() - latest.timestamp

    async def clear_cache(self, symbol: str | None = None):
        """Clear feature cache"""
        await self.connect()

        if symbol:
            # Clear specific symbol
            await self._client.delete(f"features:{symbol}")
            if symbol in self._buffer:
                del self._buffer[symbol]
        else:
            # Clear all
            pattern = "features:*"
            cursor = 0
            while True:
                cursor, keys = await self._client.scan(cursor, match=pattern, count=100)
                if keys:
                    await self._client.delete(*keys)
                if cursor == 0:
                    break

            self._buffer.clear()


# Feature calculation utilities
def calculate_vwap_deviation(price: float, vwap: float) -> float:
    """Calculate VWAP deviation in basis points"""
    if vwap == 0:
        return 0.0
    return ((price - vwap) / vwap) * 10000


def calculate_zscore(value: float, mean: float, std: float) -> float:
    """Calculate z-score"""
    if std == 0:
        return 0.0
    return (value - mean) / std


def calculate_volume_ratio(current_vol: float, avg_vol: float) -> float:
    """Calculate volume ratio"""
    if avg_vol == 0:
        return 1.0
    return current_vol / avg_vol


def calculate_order_flow_imbalance(buy_volume: float, sell_volume: float) -> float:
    """
    Calculate order flow imbalance

    Returns:
        Value between -1 (all sells) and 1 (all buys)
    """
    total = buy_volume + sell_volume
    if total == 0:
        return 0.0
    return (buy_volume - sell_volume) / total


def detect_regime(returns: np.ndarray, volatility: float) -> int:
    """
    Detect market regime

    Returns:
        0 = ranging, 1 = trending, 2 = volatile
    """
    if len(returns) < 20:
        return 0

    # Trend strength (using autocorrelation)
    autocorr = np.corrcoef(returns[:-1], returns[1:])[0, 1]

    # Volatility threshold
    vol_threshold_high = 0.03

    if volatility > vol_threshold_high:
        return 2  # Volatile
    elif abs(autocorr) > 0.3:
        return 1  # Trending
    else:
        return 0  # Ranging


def detect_volatility_regime(volatility: float) -> int:
    """
    Detect volatility regime

    Returns:
        0 = low, 1 = medium, 2 = high
    """
    if volatility < 0.01:
        return 0
    elif volatility < 0.02:
        return 1
    else:
        return 2


# Singleton instance
_store: FeatureStore | None = None


def get_feature_store(redis_url: str = "redis://localhost:6379/0") -> FeatureStore:
    """Get global feature store instance"""
    global _store
    if _store is None:
        _store = FeatureStore(redis_url)
    return _store


if __name__ == "__main__":
    import asyncio

    async def test():
        store = get_feature_store()

        # Create test features
        features = FeatureVector(
            symbol="BTCUSDT",
            timestamp=time.time(),
            price=50000.0,
            vwap_dev=5.2,
            zscore=0.8,
            atr=150.5,
            rsi=62.3,
            vol_ratio=1.2,
            vol_imbalance=0.15,
            spread_bps=2.5,
            ofi=0.3,
            regime=1,
            volatility_regime=1,
        )

        # Store
        await store.store_features("BTCUSDT", features)
        print("✅ Stored features")

        # Retrieve
        latest = await store.get_latest_features("BTCUSDT")
        print(f"📊 Latest features: {latest}")

        # Get as array
        arr = await store.get_features_array("BTCUSDT", window_size=1)
        print(f"🔢 Feature array shape: {arr.shape}")

        await store.disconnect()

    asyncio.run(test())
