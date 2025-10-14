"""
Sentiment extraction using Gemma-3 API (or mock for development).
"""

import random

from ..utils.cache import JsonCache
from ..utils.rate_limit import TokenBucket


class SentimentProvider:
    """
    Abstract sentiment provider interface.
    
    Implementations can use different LLMs/APIs:
    - Gemma-3 (Google AI Studio)
    - OpenAI GPT
    - Local transformers models
    """
    
    async def score_batch(self, texts: list[str]) -> list[float]:
        """
        Score a batch of texts.
        
        Args:
            texts: List of text snippets (news, tweets, etc.)
        
        Returns:
            List of sentiment scores (-1.0 to 1.0)
            -1.0 = very negative, 0.0 = neutral, 1.0 = very positive
        """
        raise NotImplementedError


class GemmaSentimentProvider(SentimentProvider):
    """
    Gemma-3 API sentiment provider.
    
    TODO: Implement real Gemma-3 API calls.
    Currently returns mock scores for development.
    """
    
    def __init__(self, api_key: str | None = None, rpm: int = 60):
        """
        Args:
            api_key: Gemma API key (optional for mock)
            rpm: Requests per minute limit
        """
        self.api_key = api_key
        self.bucket = TokenBucket(rate_per_min=rpm, burst=max(3, rpm // 4))
    
    async def score_batch(self, texts: list[str]) -> list[float]:
        """
        Score texts using Gemma-3 API.
        
        TODO: Implement actual API call:
        1. Batch texts into chunks of 100
        2. Send to Gemma-3 API
        3. Parse sentiment scores
        4. Handle rate limits & errors
        
        Current: Returns mock scores
        """
        scores = []
        
        for text in texts:
            # Check rate limit
            if not self.bucket.allow():
                # Rate limited - return neutral score
                # TODO: Implement proper backoff/queue
                scores.append(0.0)
                continue
            
            # TODO: Real API call here
            # score = await self._call_gemma_api(text)
            
            # Mock: Random sentiment score
            score = random.uniform(-1.0, 1.0)
            scores.append(score)
        
        return scores
    
    async def _call_gemma_api(self, text: str) -> float:
        """
        Call Gemma-3 API for a single text.
        
        TODO: Implement
        """
        # Example API call structure:
        # response = await httpx.post(
        #     "https://generativelanguage.googleapis.com/v1beta/models/gemma-3:generateContent",
        #     headers={"Authorization": f"Bearer {self.api_key}"},
        #     json={
        #         "contents": [{
        #             "parts": [{
        #                 "text": f"Analyze sentiment (-1 to 1): {text}"
        #             }]
        #         }]
        #     }
        # )
        # return float(response.json()["score"])
        raise NotImplementedError


class SentimentExtractor:
    """
    High-level sentiment extraction with caching.
    
    Handles:
    - Batch processing
    - Result caching
    - Score normalization
    - Averaging multiple texts
    """
    
    def __init__(self, provider: SentimentProvider, ttl_seconds: int = 900):
        """
        Args:
            provider: Sentiment provider (Gemma, GPT, etc.)
            ttl_seconds: Cache TTL (default 15 minutes)
        """
        self.provider = provider
        self.cache = JsonCache(base="data/cache/sentiment", ttl_seconds=ttl_seconds)
    
    async def score(self, key: str, texts: list[str]) -> float:
        """
        Get average sentiment score for a list of texts.
        
        Args:
            key: Cache key (e.g., "BTCUSDT:2025-10-13T18:30")
            texts: List of text snippets
        
        Returns:
            Average sentiment score (-1.0 to 1.0)
        """
        # Check cache
        cache_key = f"sent:{key}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return float(cached)
        
        # No texts = neutral
        if not texts:
            return 0.0
        
        # Score batch
        scores = await self.provider.score_batch(texts)
        
        # Average
        mean_score = sum(scores) / len(scores)
        
        # Cache result
        self.cache.set(cache_key, mean_score)
        
        return mean_score
    
    async def score_single(self, text: str) -> float:
        """Score a single text (convenience method)."""
        return await self.score(f"single:{hash(text)}", [text])

