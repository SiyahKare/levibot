"""
AI Prompts for signal extraction and analysis.
"""

SIGNAL_EXTRACTOR_PROMPT = """
You are a crypto trading signal parser. Extract trading information from text.

Return ONLY valid JSON with this exact structure:
{
  "symbol": "BTCUSDT",
  "side": "buy|sell",
  "size_hint": 0.1,
  "sl": null,
  "tp": null,
  "confidence": 0.0-1.0,
  "rationale": "brief explanation"
}

Rules:
- symbol: Normalized (BTCUSDT, ETHUSDT, etc.)
- side: "buy" or "sell" only
- size_hint: Suggested position size (fraction of capital, 0.01-1.0)
- sl/tp: Stop loss and take profit prices (null if not mentioned)
- confidence: Your confidence in this signal (0.0 = none, 1.0 = very high)
- rationale: One sentence why this is a valid signal

Text to analyze:
{text}

Return ONLY the JSON object, no other text.
"""

RISK_EXPLAIN_PROMPT = """
You are a risk management expert. Analyze the current portfolio state and explain risk factors.

Current state:
{metrics}

Provide:
1. Current risk level (low/medium/high)
2. Top 3 risk factors
3. Recommended actions

Return JSON:
{
  "risk_level": "low|medium|high",
  "factors": ["factor 1", "factor 2", "factor 3"],
  "actions": ["action 1", "action 2"]
}
"""

DAY_SUMMARY_PROMPT = """
Summarize today's trading activity in 2-3 sentences.

Trades: {trades}
PnL: {pnl}
Positions: {positions}

Focus on:
- Overall performance
- Notable wins/losses
- Key patterns
"""







