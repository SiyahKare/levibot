"""
Adaptive Policy v2

Volatility and regime-aware position sizing and threshold adjustment.
"""


def size_from_confidence(
    confidence: float,
    volatility: float,
    regime_multiplier: float = 1.0,
    base_size: float = 1.0,
    min_size: float = 0.0,
    max_size: float = 1.0,
) -> float:
    """
    Calculate position size based on confidence, volatility, and regime.
    
    Args:
        confidence: Model confidence [0, 1]
        volatility: Realized volatility (std of returns)
        regime_multiplier: Regime-based adjustment [0.5, 1.5]
            - trend: 1.2-1.5 (increase size)
            - neutral: 1.0 (neutral)
            - mean-reversion: 0.5-0.8 (reduce size)
        base_size: Base position size
        min_size: Minimum size
        max_size: Maximum size
    
    Returns:
        Adjusted position size
    
    Formula:
        size = base * confidence * (1 / (1 + k*vol)) * regime_multiplier
        
        Where k=5 is volatility scaling factor
    """
    if volatility <= 0:
        return 0.0
    
    # Volatility-scaled sizing (inverse relationship)
    vol_factor = 1.0 / (1.0 + 5.0 * volatility)
    
    # Combined sizing
    raw_size = base_size * confidence * vol_factor * regime_multiplier
    
    # Clamp to bounds
    return max(min_size, min(max_size, raw_size))


def adaptive_entry_threshold(
    base_threshold: float,
    regime: str,
    volatility: float,
) -> float:
    """
    Adjust entry threshold based on regime and volatility.
    
    Args:
        base_threshold: Base entry threshold (e.g., 0.55)
        regime: Market regime ("trend", "neutral", "meanrev")
        volatility: Current volatility
    
    Returns:
        Adjusted entry threshold
    
    Logic:
        - Trend regime: Lower threshold (easier entry, ride momentum)
        - Mean-reversion: Higher threshold (pickier entry, wait for extremes)
        - High volatility: Raise threshold (avoid false signals)
    """
    adjustment = 0.0
    
    # Regime adjustment
    if regime == "trend":
        adjustment -= 0.02  # Easier entry in trends
    elif regime == "meanrev":
        adjustment += 0.02  # Harder entry in choppy markets
    
    # Volatility adjustment (higher vol → higher threshold)
    if volatility > 0.03:  # High volatility
        adjustment += 0.01
    elif volatility < 0.01:  # Low volatility
        adjustment -= 0.01
    
    return base_threshold + adjustment


def adaptive_exit_threshold(
    base_threshold: float,
    regime: str,
    volatility: float,
) -> float:
    """
    Adjust exit threshold based on regime and volatility.
    
    Args:
        base_threshold: Base exit threshold (e.g., 0.45)
        regime: Market regime
        volatility: Current volatility
    
    Returns:
        Adjusted exit threshold
    
    Logic:
        - Trend regime: Lower exit (let winners run)
        - Mean-reversion: Higher exit (take profits faster)
        - High volatility: Adjust exit wider to avoid noise
    """
    adjustment = 0.0
    
    # Regime adjustment
    if regime == "trend":
        adjustment -= 0.02  # Hold longer in trends
    elif regime == "meanrev":
        adjustment += 0.02  # Exit faster in chop
    
    # Volatility adjustment
    if volatility > 0.03:
        adjustment -= 0.01  # Wider stop in volatile markets
    elif volatility < 0.01:
        adjustment += 0.01  # Tighter stop in calm markets
    
    return base_threshold + adjustment


def adaptive_stop_loss(
    entry_price: float,
    base_stop_pct: float,
    volatility: float,
) -> float:
    """
    Calculate adaptive stop loss based on volatility.
    
    Args:
        entry_price: Entry price
        base_stop_pct: Base stop loss percentage (e.g., 0.03 = 3%)
        volatility: Current volatility
    
    Returns:
        Stop loss price
    
    Logic:
        Higher volatility → wider stop (avoid noise)
        Lower volatility → tighter stop (protect capital)
    """
    # Adjust stop based on volatility (1-3x base)
    vol_multiplier = 1.0 + min(2.0, volatility / 0.01)  # 1x to 3x
    
    adjusted_stop_pct = base_stop_pct * vol_multiplier
    
    return entry_price * (1.0 - adjusted_stop_pct)


def adaptive_take_profit(
    entry_price: float,
    base_tp_pct: float,
    confidence: float,
    volatility: float,
) -> float:
    """
    Calculate adaptive take profit based on confidence and volatility.
    
    Args:
        entry_price: Entry price
        base_tp_pct: Base take profit percentage (e.g., 0.05 = 5%)
        confidence: Model confidence [0, 1]
        volatility: Current volatility
    
    Returns:
        Take profit price
    
    Logic:
        High confidence → wider TP (let it run)
        Low confidence → tighter TP (take what you can get)
        High volatility → adjust TP to realistic levels
    """
    # Confidence adjustment (0.5x to 2x)
    conf_multiplier = 0.5 + confidence * 1.5
    
    # Volatility adjustment (wider TP in volatile markets)
    vol_multiplier = 1.0 + min(1.0, volatility / 0.02)
    
    adjusted_tp_pct = base_tp_pct * conf_multiplier * vol_multiplier
    
    return entry_price * (1.0 + adjusted_tp_pct)


def classify_regime(
    returns: list[float],
    volatility: float,
    trend_strength: float = 0.0,
) -> str:
    """
    Classify market regime.
    
    Args:
        returns: Recent returns
        volatility: Current volatility
        trend_strength: Optional trend indicator
    
    Returns:
        "trend", "neutral", or "meanrev"
    
    Logic:
        - Strong trend + low vol → "trend"
        - High vol + no trend → "meanrev"
        - Otherwise → "neutral"
    """
    if not returns or len(returns) < 10:
        return "neutral"
    
    # Calculate trend (cumulative return)
    cumulative_return = sum(returns)
    abs_return = abs(cumulative_return)
    
    # Thresholds
    TREND_THRESHOLD = 0.02  # 2% cumulative
    VOL_THRESHOLD = 0.025  # 2.5% volatility
    
    if abs_return > TREND_THRESHOLD and volatility < VOL_THRESHOLD:
        return "trend"
    elif volatility > VOL_THRESHOLD and abs_return < TREND_THRESHOLD / 2:
        return "meanrev"
    else:
        return "neutral"

