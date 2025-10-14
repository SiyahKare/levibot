"""
OpenAI AI Brain Client (with Rate Limiting & Secret Masking)
Handles news scoring, regime advice, and anomaly explanation
"""

import hashlib
import json
import os
import time
from pathlib import Path
from threading import Lock
from typing import Any

from openai import OpenAI

from ..infra.settings import settings

# Initialize OpenAI client
_client = None

# Rate limiter state (simple token bucket)
_rate_limiter = {
    "tokens": settings.OPENAI_RPM,
    "last_refill": time.time(),
    "lock": Lock(),
}

# Token budget tracker (monthly)
_ai_tokens_month = {
    "month": None,
    "used": 0,
    "lock": Lock(),
}


def mask_secret(text: str, show_chars: int = 4) -> str:
    """
    Mask sensitive strings in logs.

    Args:
        text: Text to mask
        show_chars: Number of chars to show at start/end

    Returns:
        Masked string like "sk-ab...xyz"
    """
    if not settings.MASK_SECRETS_IN_LOGS or not text or len(text) <= show_chars * 2:
        return text

    return f"{text[:show_chars]}...{text[-show_chars:]}"


def rate_limit_check():
    """
    Simple token bucket rate limiter for OpenAI calls.
    Raises RateLimitError if rate limit exceeded.
    """
    with _rate_limiter["lock"]:
        now = time.time()
        elapsed = now - _rate_limiter["last_refill"]

        # Refill tokens based on elapsed time (RPM = tokens/60sec)
        refill_amount = (elapsed / 60.0) * settings.OPENAI_RPM
        _rate_limiter["tokens"] = min(
            settings.OPENAI_RPM, _rate_limiter["tokens"] + refill_amount
        )
        _rate_limiter["last_refill"] = now

        # Check if we have tokens available
        if _rate_limiter["tokens"] < 1.0:
            wait_time = (1.0 - _rate_limiter["tokens"]) * (60.0 / settings.OPENAI_RPM)
            raise RateLimitError(f"OpenAI rate limit exceeded. Wait {wait_time:.1f}s")

        # Consume one token
        _rate_limiter["tokens"] -= 1.0


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""

    pass


def get_client() -> OpenAI:
    """Get or create OpenAI client."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        _client = OpenAI(api_key=api_key)
    return _client


def cached(cache_dir: str, key: str, fn: callable) -> Any:
    """
    Cache helper for OpenAI responses.

    Args:
        cache_dir: Cache directory path
        key: Cache key (will be hashed)
        fn: Function to call if cache miss

    Returns:
        Cached or fresh result
    """
    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    cache_file = cache_path / f"{hashlib.md5(key.encode()).hexdigest()}.json"

    if cache_file.exists():
        try:
            with open(cache_file) as f:
                return json.load(f)
        except Exception:
            pass  # Cache corrupted, regenerate

    result = fn()

    try:
        with open(cache_file, "w") as f:
            json.dump(result, f, indent=2)
    except Exception:
        pass  # Cache write failed, continue anyway

    return result


def score_headline(headline: str) -> dict[str, Any]:
    """
    Score a single news headline for crypto impact.

    Args:
        headline: News headline text

    Returns:
        Structured impact data: {asset, event_type, impact, horizon, confidence}
    """

    def call():
        rate_limit_check()  # Check rate limit before API call
        cli = get_client()
        prompt = (
            f"Crypto headline: {headline}\n\n"
            "Analyze this headline and return ONLY a compact JSON with these fields:\n"
            "- asset: string (e.g., 'BTC', 'ETH', 'SOL', or 'MKT' for market-wide)\n"
            "- event_type: string (e.g., 'regulation', 'hack', 'adoption', 'macro')\n"
            "- impact: number from -1 (very bearish) to +1 (very bullish)\n"
            "- horizon: string, one of: 'intra', 'daily', 'weekly'\n"
            "- confidence: number from 0 (uncertain) to 1 (very confident)\n\n"
            "Respond ONLY with valid JSON, no explanation."
        )

        try:
            resp = cli.chat.completions.create(
                model="gpt-4o-mini",  # Cost-effective, fast
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=120,
            )

            txt = resp.choices[0].message.content.strip()

            # Try to extract JSON from response
            if "```json" in txt:
                txt = txt.split("```json")[1].split("```")[0].strip()
            elif "```" in txt:
                txt = txt.split("```")[1].split("```")[0].strip()

            return json.loads(txt)

        except Exception as e:
            # Fallback on error
            return {
                "asset": "MKT",
                "event_type": "unknown",
                "impact": 0.0,
                "horizon": "intra",
                "confidence": 0.5,
                "error": str(e),
            }

    return cached("backend/data/cache/news", headline, call)


def score_headlines(headlines: list[str]) -> list[dict[str, Any]]:
    """
    Score multiple headlines (uses cache for deduplication).

    Args:
        headlines: List of news headline texts

    Returns:
        List of structured impact data
    """
    return [score_headline(h) for h in headlines]


def regime_advice(metrics: dict[str, Any]) -> dict[str, Any]:
    """
    Get regime-based trading advice from AI.

    Args:
        metrics: Current market metrics (volatility, trend, ECE, PSI, PnL, etc.)

    Returns:
        Regime advice: {regime, risk_multiplier, entry_delta, exit_delta, reason}
    """
    rate_limit_check()  # Check rate limit before API call
    cli = get_client()

    system_prompt = (
        "You are a strict risk/regime advisor for cryptocurrency quantitative trading.\n"
        "Your role is to adjust position sizing and entry/exit thresholds based on market conditions.\n\n"
        "Given market metrics (JSON), output a JSON response with:\n"
        "- regime: string, one of 'trend', 'neutral', 'meanrev'\n"
        "- risk_multiplier: number from 0.5 to 1.5 (adjust position sizing)\n"
        "- entry_delta: number from -0.02 to +0.02 (adjust entry threshold)\n"
        "- exit_delta: number from -0.02 to +0.02 (adjust exit threshold)\n"
        "- reason: string, brief explanation (max 100 chars)\n\n"
        "Be CONSERVATIVE. Never exceed the bounds. Respond ONLY with valid JSON."
    )

    user_prompt = f"Market metrics:\n{json.dumps(metrics, indent=2)}"

    try:
        resp = cli.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=160,
        )

        txt = resp.choices[0].message.content.strip()

        # Try to extract JSON
        if "```json" in txt:
            txt = txt.split("```json")[1].split("```")[0].strip()
        elif "```" in txt:
            txt = txt.split("```")[1].split("```")[0].strip()

        result = json.loads(txt)

        # Validate and clamp
        result["risk_multiplier"] = max(
            0.5, min(1.5, float(result.get("risk_multiplier", 1.0)))
        )
        result["entry_delta"] = max(
            -0.02, min(0.02, float(result.get("entry_delta", 0.0)))
        )
        result["exit_delta"] = max(
            -0.02, min(0.02, float(result.get("exit_delta", 0.0)))
        )

        return result

    except Exception as e:
        # Fallback on error
        return {
            "regime": "neutral",
            "risk_multiplier": 1.0,
            "entry_delta": 0.0,
            "exit_delta": 0.0,
            "reason": f"fallback: {str(e)[:50]}",
        }


def explain_anomaly(context: dict[str, Any]) -> dict[str, Any]:
    """
    Explain an anomaly and provide runbook suggestions.

    Args:
        context: Anomaly context (PSI, ECE, PnL, staleness, etc.)

    Returns:
        Explanation: {cause, runbook, severity}
    """
    rate_limit_check()  # Check rate limit before API call
    cli = get_client()

    system_prompt = (
        "You are a production ML system debugger for crypto trading.\n"
        "Given anomaly indicators, provide:\n"
        "- cause: string, likely root cause (max 200 chars)\n"
        "- runbook: list[string], actionable steps to fix (max 5 steps)\n"
        "- severity: string, one of 'low', 'medium', 'high', 'critical'\n\n"
        "Respond ONLY with valid JSON."
    )

    user_prompt = f"Anomaly context:\n{json.dumps(context, indent=2)}"

    try:
        resp = cli.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=300,
        )

        txt = resp.choices[0].message.content.strip()

        # Try to extract JSON
        if "```json" in txt:
            txt = txt.split("```json")[1].split("```")[0].strip()
        elif "```" in txt:
            txt = txt.split("```")[1].split("```")[0].strip()

        return json.loads(txt)

    except Exception as e:
        # Fallback on error
        return {
            "cause": f"AI analysis failed: {str(e)[:100]}",
            "runbook": ["Check logs", "Verify data pipeline", "Contact support"],
            "severity": "medium",
        }


def extract_signal_from_text(text: str) -> dict[str, Any]:
    """
    Extract trading signal from raw text (e.g., Telegram message).

    Args:
        text: Raw signal text

    Returns:
        Parsed signal: {symbol, side, size_hint, sl, tp, confidence, rationale}
    """
    from .prompts import SIGNAL_EXTRACTOR_PROMPT

    rate_limit_check()  # Check rate limit before API call
    cli = get_client()

    try:
        resp = cli.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You output ONLY valid JSON. No markdown, no explanations.",
                },
                {
                    "role": "user",
                    "content": SIGNAL_EXTRACTOR_PROMPT.format(text=text[:1000]),
                },
            ],
            temperature=0.1,
            max_tokens=200,
        )

        txt = resp.choices[0].message.content.strip()

        # Remove markdown code blocks
        if "```json" in txt:
            txt = txt.split("```json")[1].split("```")[0].strip()
        elif "```" in txt:
            txt = txt.split("```")[1].split("```")[0].strip()

        result = json.loads(txt)

        # Validate and set defaults
        result.setdefault("symbol", "UNKNOWN")
        result.setdefault("side", "buy")
        result.setdefault("size_hint", 0.01)
        result.setdefault("confidence", 0.0)
        result.setdefault("rationale", "")

        return result

    except Exception as e:
        return {
            "symbol": "UNKNOWN",
            "side": "buy",
            "size_hint": 0.0,
            "confidence": 0.0,
            "rationale": f"Error: {str(e)}",
        }


def _month_key() -> str:
    """Get current month key for budget tracking (YYYY-MM)."""
    from datetime import datetime

    now = datetime.utcnow()
    return f"{now.year}-{now.month:02d}"


def _budget_ok() -> bool:
    """Check if monthly token budget has not been exceeded."""
    with _ai_tokens_month["lock"]:
        mk = _month_key()
        if _ai_tokens_month["month"] != mk:
            # New month, reset counter
            _ai_tokens_month["month"] = mk
            _ai_tokens_month["used"] = 0

        return _ai_tokens_month["used"] < settings.AI_REASON_MONTHLY_TOKEN_BUDGET


def _acc_tokens(n: int) -> None:
    """Accumulate token usage for budget tracking."""
    with _ai_tokens_month["lock"]:
        mk = _month_key()
        if _ai_tokens_month["month"] != mk:
            _ai_tokens_month["month"] = mk
            _ai_tokens_month["used"] = 0

        _ai_tokens_month["used"] += max(0, n)


def brief_reason(
    symbol: str,
    side: str,
    qty: float,
    mark: float,
    confidence: float = 0.0,
    excerpt: str = "",
) -> str:
    """
    Generate brief trade reason (1-2 sentences).

    Args:
        symbol: Trading pair
        side: buy or sell
        qty: Quantity
        mark: Mark price
        confidence: Signal confidence (0-1)
        excerpt: Brief context

    Returns:
        Plain text explanation
    """
    from .prompts.trade_reason import TRADE_REASON_PROMPT

    rate_limit_check()
    cli = get_client()

    prompt = TRADE_REASON_PROMPT.format(
        symbol=symbol,
        side=side,
        qty=qty,
        mark=mark,
        confidence=confidence,
        excerpt=excerpt[:240],
    )

    try:
        resp = cli.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=80,
        )

        return resp.choices[0].message.content.strip()

    except Exception:
        return f"Trade executed based on signal (confidence: {confidence:.2f})"


def brief_reason_plus(
    symbol: str,
    side: str,
    qty: float,
    mark: float,
    confidence: float = 0.0,
    excerpt: str = "",
    ctx: dict[str, Any] | None = None,
    timeout_s: float | None = None,
) -> str:
    """
    Enhanced trade reason with market context, budget tracking, and timeout.

    Args:
        symbol: Trading pair
        side: buy or sell
        qty: Quantity
        mark: Mark price
        confidence: Signal confidence (0-1)
        excerpt: Brief context
        ctx: Market context dict (last_px, ret_1m, spread_bps)
        timeout_s: Timeout in seconds (default from settings)

    Returns:
        Plain text explanation
    """
    # Check if AI reason is enabled
    if not settings.AI_REASON_ENABLED:
        return "-"

    # Check monthly budget
    if not _budget_ok():
        return "-"

    timeout = timeout_s or settings.AI_REASON_TIMEOUT_S
    context = ctx or {}

    last_px = context.get("last_px")
    ret_1m = context.get("ret_1m")
    spread_bps = context.get("spread_bps")

    # Build enhanced prompt with market context
    prompt = (
        "You are a trading analyst. In <=2 sentences, explain the rationale for this trade.\n"
        f"symbol={symbol}, side={side}, qty={qty}, fill={mark}\n"
        f"signal_confidence={confidence:.2f}\n"
        f"market.last={last_px}, market.ret_1m={ret_1m}, spread_bps={spread_bps}\n"
        f"context_excerpt={excerpt[:240]}\n"
        "No disclaimers, no emojis, no JSON."
    )

    # Time-boxed completion
    import threading

    result = ["-"]  # Mutable container for thread result

    def _run():
        try:
            rate_limit_check()
            cli = get_client()

            resp = cli.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=80,
            )

            # Estimate tokens: prompt/4 + output
            est_tokens = len(prompt) // 4 + 80
            _acc_tokens(est_tokens)

            result[0] = resp.choices[0].message.content.strip()

        except Exception:
            result[0] = "-"

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        # Timeout exceeded
        return "-"

    return result[0] or "-"


def telegram_ai_answer(
    question: str,
    signals: list[dict[str, Any]] | None = None,
    metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Answer operator question about telegram signals using OpenAI."""

    if not question.strip():
        raise ValueError("question is empty")

    rate_limit_check()  # Check rate limit before API call
    cli = get_client()

    signals = signals or []
    lines: list[str] = []
    for item in signals[:12]:
        try:
            ts = item.get("ts", "")
            chat = item.get("chat_title", "?")
            symbol = item.get("symbol", "?")
            side = item.get("side", "?")
            conf = item.get("confidence")
            conf_txt = f"{float(conf):.0%}" if isinstance(conf, (int, float)) else "n/a"
            lines.append(f"{ts} | {chat} | {symbol} | {side} | confidence={conf_txt}")
        except Exception:
            continue

    signals_block = "\n".join(lines) if lines else "(no recent signals provided)"
    metrics_block = (
        json.dumps(metrics or {}, indent=2) if metrics else "(no metrics provided)"
    )

    system_prompt = (
        "You are LeviBot's Telegram GPT analyst."
        " Analyse recent Telegram trading signals, group reputation, and risk metrics."
        " Provide concise tactical guidance for the trading team."
        " Always respond with valid JSON containing:"
        " answer (string), reasoning (string), recommendations (array of strings)."
        " Recommendations list must have between 1 and 5 actionable bullet points."
    )

    user_prompt = (
        f"Operator question: {question.strip()}\n\n"
        f"Recent Telegram signals (latest first):\n{signals_block}\n\n"
        f"Supplementary metrics:\n{metrics_block}\n"
    )

    try:
        resp = cli.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
            max_tokens=320,
        )

        txt = resp.choices[0].message.content.strip()

        if "```json" in txt:
            txt = txt.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in txt:
            txt = txt.split("```", 1)[1].split("```", 1)[0].strip()

        parsed = json.loads(txt)

        answer = str(parsed.get("answer", ""))
        reasoning = str(parsed.get("reasoning", ""))
        recs = parsed.get("recommendations")
        if not isinstance(recs, list):
            recs = [str(parsed.get("recommendations", ""))]
        recs = [str(r) for r in recs if str(r).strip()]
        if not answer.strip():
            raise ValueError("AI returned empty answer")

        return {
            "answer": answer.strip(),
            "reasoning": reasoning.strip(),
            "recommendations": recs or ["Monitor channels for more context"],
        }

    except json.JSONDecodeError as e:
        raise ValueError(f"AI response parse failed: {e}") from e
    except Exception as e:
        return {
            "answer": "Unable to generate guidance right now.",
            "reasoning": str(e)[:120],
            "recommendations": [
                "Review recent Telegram signals manually",
                "Ensure OpenAI API key is configured",
            ],
        }
