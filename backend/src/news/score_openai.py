"""
OpenAI Sentiment Scorer

Use OpenAI structured outputs to score news headlines for crypto impact.
"""

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from openai import OpenAI

# Cache directory for scored headlines
CACHE_DIR = Path("backend/data/cache/sentiment")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_openai_client() -> OpenAI | None:
    """Get OpenAI client if API key is configured."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def score_headline(headline: str, client: OpenAI | None = None) -> dict[str, Any]:
    """
    Score a single headline using OpenAI structured output.

    Args:
        headline: News headline text
        client: Optional OpenAI client (will create if None)

    Returns:
        {
            "asset": str,           # e.g., "BTC", "ETH", "MKT" (market-wide)
            "impact": float,        # [-1.0, 1.0] negative/positive
            "horizon": str,         # "intra", "daily", "weekly"
            "confidence": float,    # [0.0, 1.0]
            "cached": bool,
        }
    """
    # Check cache first
    cache_key = hashlib.md5(headline.encode()).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.json"

    if cache_file.exists():
        with open(cache_file) as f:
            result = json.load(f)
            result["cached"] = True
            return result

    # Call OpenAI if client available
    if client is None:
        client = get_openai_client()

    if client is None:
        # No API key, return neutral
        return {
            "asset": "MKT",
            "impact": 0.0,
            "horizon": "intra",
            "confidence": 0.0,
            "cached": False,
        }

    try:
        # Use structured JSON output
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cheap for this task
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a crypto news analyst. Score headlines for their impact on crypto assets. "
                        "Return JSON with: asset (BTC/ETH/SOL/MKT), impact (-1.0 to 1.0), horizon (intra/daily/weekly), confidence (0.0 to 1.0)."
                    ),
                },
                {"role": "user", "content": headline},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=150,
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from OpenAI")

        result = json.loads(content)

        # Validate and normalize
        result = {
            "asset": str(result.get("asset", "MKT")),
            "impact": float(max(-1.0, min(1.0, result.get("impact", 0.0)))),
            "horizon": str(result.get("horizon", "intra")),
            "confidence": float(max(0.0, min(1.0, result.get("confidence", 0.5)))),
            "cached": False,
        }

        # Cache result
        with open(cache_file, "w") as f:
            json.dump(result, f)

        return result

    except Exception as e:
        # Fallback to neutral on error
        return {
            "asset": "MKT",
            "impact": 0.0,
            "horizon": "intra",
            "confidence": 0.0,
            "error": str(e),
            "cached": False,
        }


def score_headlines(headlines: list[str]) -> list[dict[str, Any]]:
    """
    Score multiple headlines with shared client.

    Args:
        headlines: List of headline strings

    Returns:
        List of score dictionaries
    """
    client = get_openai_client()
    results = []

    for headline in headlines:
        result = score_headline(headline, client=client)
        results.append(result)

    return results


def get_cache_stats() -> dict[str, Any]:
    """Get sentiment cache statistics."""
    cache_files = list(CACHE_DIR.glob("*.json"))

    total_cached = len(cache_files)
    total_size_kb = sum(f.stat().st_size for f in cache_files) / 1024

    return {
        "cached_headlines": total_cached,
        "cache_size_kb": round(total_size_kb, 2),
        "cache_dir": str(CACHE_DIR),
    }


def clear_cache():
    """Clear sentiment cache (useful for testing)."""
    for cache_file in CACHE_DIR.glob("*.json"):
        cache_file.unlink()
