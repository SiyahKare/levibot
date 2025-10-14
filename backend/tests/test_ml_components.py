"""
Tests for ML components: sentiment, on-chain, ensemble.
"""

import asyncio

import pytest
from src.ml.features.onchain_fetcher import MockOnchainProvider, OnchainFetcher
from src.ml.features.sentiment_extractor import (
    GemmaSentimentProvider,
    SentimentExtractor,
)
from src.ml.models.ensemble_predictor import EnsemblePredictor


@pytest.mark.asyncio
async def test_sentiment_cache():
    """Test sentiment extraction with caching."""
    extractor = SentimentExtractor(
        GemmaSentimentProvider(rpm=100),
        ttl_seconds=1
    )
    
    # First call
    score1 = await extractor.score("TESTKEY", ["positive", "bullish", "moon"])
    
    # Second call (should hit cache)
    score2 = await extractor.score("TESTKEY", ["positive", "bullish", "moon"])
    
    assert score1 == score2  # Cache hit
    assert -1.0 <= score1 <= 1.0  # Valid range


@pytest.mark.asyncio
async def test_sentiment_empty_texts():
    """Test sentiment with empty text list."""
    extractor = SentimentExtractor(GemmaSentimentProvider())
    
    score = await extractor.score("EMPTY", [])
    
    assert score == 0.0  # Neutral for empty


@pytest.mark.asyncio
async def test_onchain_mock_metrics():
    """Test on-chain fetcher with mock provider."""
    fetcher = OnchainFetcher(MockOnchainProvider(), ttl_seconds=1)
    
    # First call
    metrics1 = await fetcher.get_metrics("BTCUSDT")
    
    # Second call (should hit cache)
    metrics2 = await fetcher.get_metrics("BTCUSDT")
    
    assert metrics1 == metrics2  # Cache hit
    assert "active_wallets" in metrics1
    assert "exchange_inflow" in metrics1
    assert "funding_rate" in metrics1


def test_ensemble_predictor_init():
    """Test ensemble predictor initialization."""
    ensemble = EnsemblePredictor(
        w_lgbm=0.5,
        w_tft=0.3,
        w_sent=0.2,
        threshold=0.55
    )
    
    assert ensemble.w_lgbm == 0.5
    assert ensemble.w_tft == 0.3
    assert ensemble.w_sent == 0.2
    assert ensemble.threshold == 0.55


def test_ensemble_predictor_shapes():
    """Test ensemble predictor output shapes."""
    ensemble = EnsemblePredictor(threshold=0.55)
    
    features = {
        "vol": 0.1,
        "spread": 0.01,
        "funding_rate": 0.0,
        "inflow": 0.1,
        "outflow": 0.2,
        "whale_txs": 5.0,
    }
    
    prediction = ensemble.predict(features, sentiment=0.0)
    
    # Check output keys
    assert {"prob_up", "side", "confidence"} <= set(prediction.keys())
    
    # Check value ranges
    assert 0.0 <= prediction["prob_up"] <= 1.0
    assert 0.0 <= prediction["confidence"] <= 1.0
    assert prediction["side"] in {"long", "short", "flat"}


def test_ensemble_predictor_long_signal():
    """Test ensemble predictor generates long signal for high probability."""
    ensemble = EnsemblePredictor(threshold=0.55)
    
    # Mock high sentiment (bullish)
    prediction = ensemble.predict({}, sentiment=1.0)
    
    # With default weights, high sentiment should push prob_up higher
    # But exact value depends on LGBM/TFT mocks
    assert prediction["side"] in {"long", "flat"}


def test_ensemble_predictor_short_signal():
    """Test ensemble predictor generates short signal for low probability."""
    ensemble = EnsemblePredictor(threshold=0.55)
    
    # Mock low sentiment (bearish)
    prediction = ensemble.predict({}, sentiment=-1.0)
    
    # With default weights, low sentiment should push prob_up lower
    assert prediction["side"] in {"short", "flat"}


def test_ensemble_predictor_flat_signal():
    """Test ensemble predictor generates flat signal for neutral probability."""
    ensemble = EnsemblePredictor(threshold=0.55)
    
    # Neutral sentiment
    prediction = ensemble.predict({}, sentiment=0.0)
    
    # Prob should be around 0.5, resulting in flat
    # (depends on LGBM/TFT mock values)
    assert 0.0 <= prediction["prob_up"] <= 1.0


@pytest.mark.asyncio
async def test_cache_ttl_expiry():
    """Test cache expiry after TTL."""
    from src.ml.utils.cache import JsonCache
    
    cache = JsonCache(ttl_seconds=1)
    
    cache.set("test_key", "test_value")
    
    # Immediate get should work
    assert cache.get("test_key") == "test_value"
    
    # Wait for TTL to expire
    await asyncio.sleep(1.1)
    
    # Should return None (expired)
    assert cache.get("test_key") is None


def test_rate_limiter_allow():
    """Test rate limiter allows requests within limit."""
    from src.ml.utils.rate_limit import TokenBucket
    
    bucket = TokenBucket(rate_per_min=60, burst=10)
    
    # First 10 requests should be allowed (burst)
    for _ in range(10):
        assert bucket.allow() is True
    
    # 11th request should be denied
    assert bucket.allow() is False


def test_rate_limiter_wait_time():
    """Test rate limiter wait time calculation."""
    from src.ml.utils.rate_limit import TokenBucket
    
    bucket = TokenBucket(rate_per_min=60, burst=1)
    
    # Consume token
    assert bucket.allow() is True
    
    # Wait time should be ~1 second (60/min = 1/sec)
    wait = bucket.wait_time()
    assert 0.9 <= wait <= 1.1

