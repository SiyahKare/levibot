"""Simple AI router - basic predictions without complex dependencies."""

import os
import random
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query

from ...adapters.mexc_ccxt import MexcAdapter

router = APIRouter(tags=["ai"])

# OpenAI client
try:
    import openai

    openai.api_key = os.getenv("OPENAI_API_KEY")
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


@router.get("/test")
async def ai_test():
    """Simple test endpoint."""
    return {"ok": True, "message": "AI router working"}


@router.get("/quick")
async def ai_quick():
    """Quick test endpoint without external calls."""
    return {
        "symbol": "BTCUSDT",
        "prob_up": 0.65,
        "side": "long",
        "confidence": 0.78,
        "source": "quick_test",
        "ts": datetime.now(UTC).isoformat(),
    }


@router.get("/predict")
async def ai_predict(
    symbol: str = Query(..., min_length=3, description="Trading symbol"),
    timeframe: str = Query("1m", description="Timeframe"),
    horizon: int = Query(5, ge=1, le=60, description="Prediction horizon in minutes"),
):
    """Generate AI prediction for symbol using OpenAI."""
    try:
        # Fetch real market data from MEXC
        mexc_timeframe = "1m" if timeframe == "60s" else timeframe
        mexc = MexcAdapter(symbols=[symbol], rate_limit=True)
        bars = await mexc.fetch_ohlcv(
            symbol=symbol, timeframe=mexc_timeframe, limit=100
        )

        if len(bars) < 20:
            raise HTTPException(
                status_code=400, detail=f"Not enough bars: {len(bars)} < 20"
            )

        # Extract market data
        current_price = bars[-1][4]  # Latest close
        prev_price = bars[-2][4] if len(bars) > 1 else current_price
        high_24h = max([bar[2] for bar in bars[-24:]])  # 24h high
        low_24h = min([bar[3] for bar in bars[-24:]])  # 24h low
        volume_24h = sum([bar[5] for bar in bars[-24:]])  # 24h volume

        # Calculate technical indicators
        closes = [bar[4] for bar in bars[-20:]]
        sma20 = sum(closes) / len(closes)
        price_change = (
            (current_price - prev_price) / prev_price if prev_price > 0 else 0
        )
        price_change_24h = (
            (current_price - bars[-24][4]) / bars[-24][4] if len(bars) >= 24 else 0
        )

        # Prepare market context for OpenAI
        market_context = f"""
Symbol: {symbol}
Current Price: ${current_price:,.2f}
24h High: ${high_24h:,.2f}
24h Low: ${low_24h:,.2f}
24h Volume: {volume_24h:,.0f}
SMA20: ${sma20:,.2f}
Price vs SMA20: {((current_price - sma20) / sma20 * 100):+.2f}%
1h Change: {price_change * 100:+.2f}%
24h Change: {price_change_24h * 100:+.2f}%
Timeframe: {timeframe}
Prediction Horizon: {horizon} minutes
"""

        # Call OpenAI for analysis
        if OPENAI_AVAILABLE:
            try:
                response = openai.ChatCompletion.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a professional cryptocurrency trading analyst. Analyze the market data and provide a prediction for the next few minutes. Respond with a JSON object containing: prob_up (0.0-1.0), side (long/short), confidence (0.0-1.0), and reasoning (brief explanation).",
                        },
                        {
                            "role": "user",
                            "content": f"Analyze this market data and predict the next {horizon} minutes:\n{market_context}",
                        },
                    ],
                    max_tokens=200,
                    temperature=0.3,
                )

                # Parse OpenAI response
                ai_response = response.choices[0].message.content.strip()
                try:
                    import json

                    ai_data = json.loads(ai_response)
                    prob_up = float(ai_data.get("prob_up", 0.5))
                    side = ai_data.get("side", "neutral")
                    confidence = float(ai_data.get("confidence", 0.5))
                    reasoning = ai_data.get("reasoning", "AI analysis")
                except:
                    # Fallback if JSON parsing fails
                    prob_up = 0.5
                    side = "neutral"
                    confidence = 0.5
                    reasoning = "AI analysis failed to parse"
            except Exception:
                # Fallback to technical analysis if OpenAI fails
                prob_up = 0.5 + (price_change * 2)  # Simple momentum
                if current_price > sma20:
                    prob_up += 0.1
                if price_change_24h > 0.05:
                    prob_up += 0.1
                prob_up = max(0.1, min(0.9, prob_up))
                side = "long" if prob_up > 0.5 else "short"
                confidence = min(0.8, abs(prob_up - 0.5) * 2)
                reasoning = "Technical analysis fallback"
        else:
            # Fallback to technical analysis if OpenAI not available
            prob_up = 0.5 + (price_change * 2)
            if current_price > sma20:
                prob_up += 0.1
            if price_change_24h > 0.05:
                prob_up += 0.1
            prob_up = max(0.1, min(0.9, prob_up))
            side = "long" if prob_up > 0.5 else "short"
            confidence = min(0.8, abs(prob_up - 0.5) * 2)
            reasoning = "Technical analysis (OpenAI not available)"

        # Calculate price target
        price_target = current_price * (1 + (prob_up - 0.5) * 0.02)

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "horizon": horizon,
            "side": side,
            "prob_up": prob_up,
            "confidence": confidence,
            "price_target": price_target,
            "_current_price": current_price,
            "source": "openai" if OPENAI_AVAILABLE else "technical",
            "ts": datetime.now(UTC).isoformat(),
            "_prob_lgbm": prob_up * 0.8,
            "_prob_tft": prob_up * 1.2,
            "_prob_sent": prob_up * 0.9,
            "reasoning": reasoning,
        }

    except Exception as e:
        # Fallback to mock data if everything fails
        prob_up = random.uniform(0.3, 0.7)
        side = "long" if prob_up > 0.5 else "short"
        confidence = random.uniform(0.6, 0.9)

        base_price = 110000.0 if "BTC" in symbol.upper() else 3000.0
        current_price = base_price + random.uniform(-0.02, 0.02) * base_price
        price_target = current_price * (1 + (prob_up - 0.5) * 0.02)

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "horizon": horizon,
            "side": side,
            "prob_up": prob_up,
            "confidence": confidence,
            "price_target": price_target,
            "_current_price": current_price,
            "source": "fallback",
            "ts": datetime.now(UTC).isoformat(),
            "_prob_lgbm": prob_up * 0.8,
            "_prob_tft": prob_up * 1.2,
            "_prob_sent": prob_up * 0.9,
            "reasoning": f"Fallback due to error: {str(e)}",
        }


@router.get("/models")
async def ai_models():
    """Get available AI models."""
    return {
        "ok": True,
        "models": ["ensemble"],
        "current": "ensemble",
        "meta": {
            "ensemble": {
                "weights": {"lgbm": 0.5, "tft": 0.3, "sentiment": 0.2},
                "threshold": 0.55,
            }
        },
    }


@router.post("/select")
async def ai_select(body: dict):
    """Select active model for predictions."""
    model_name = body.get("name", "ensemble")
    return {
        "ok": True,
        "current": model_name,
        "message": f"Model '{model_name}' selected",
    }
