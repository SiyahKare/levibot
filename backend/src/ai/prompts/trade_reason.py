"""
Trade Reason Prompt
Explains WHY a trade was made given signal and market context
"""

TRADE_REASON_PROMPT = """You are a trading analyst. In ≤2 sentences explain WHY this trade made sense given the signal and market.
Return plain text, no JSON, no emojis.

Context:
- Symbol: {symbol}
- Side: {side}
- Quantity: {qty}
- Mark Price: {mark}
- Signal Confidence: {confidence}
- Excerpt: {excerpt}

Explanation:"""

