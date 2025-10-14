"""
Adaptive Policy Bridge
Applies AI Brain regime advice to trading policy
"""
from typing import Any


def apply_regime(
    policy: dict[str, Any],
    regime_json: dict[str, Any],
) -> dict[str, Any]:
    """
    Apply AI regime advice to trading policy.
    
    Args:
        policy: Base trading policy with entry/exit thresholds
        regime_json: AI regime advice with deltas and multipliers
    
    Returns:
        Adjusted policy
    """
    # Extract base values
    base_entry = float(policy.get("entry_threshold", 0.55))
    base_exit = float(policy.get("exit_threshold", 0.48))
    
    # Extract AI adjustments (with fallback defaults)
    entry_delta = float(regime_json.get("entry_delta", 0.0))
    exit_delta = float(regime_json.get("exit_delta", 0.0))
    risk_mul = float(regime_json.get("risk_multiplier", 1.0))
    
    # Apply adjustments with bounds
    adjusted_entry = max(0.45, min(0.65, base_entry + entry_delta))
    adjusted_exit = max(0.35, min(0.55, base_exit + exit_delta))
    
    # Clamp risk multiplier
    risk_mul = max(0.5, min(1.5, risk_mul))
    
    # Ensure entry > exit
    if adjusted_entry <= adjusted_exit:
        adjusted_entry = adjusted_exit + 0.05
    
    return {
        **policy,
        "entry_threshold": round(adjusted_entry, 3),
        "exit_threshold": round(adjusted_exit, 3),
        "risk_multiplier": round(risk_mul, 2),
        "regime": regime_json.get("regime", "neutral"),
        "regime_reason": regime_json.get("reason", ""),
    }


def calculate_adaptive_size(
    base_notional: float,
    confidence: float,
    volatility: float,
    risk_multiplier: float = 1.0,
) -> float:
    """
    Calculate adaptive position size.
    
    Args:
        base_notional: Base position size in USD
        confidence: Model confidence (0-1)
        volatility: Market volatility (0-1+)
        risk_multiplier: AI regime risk multiplier (0.5-1.5)
    
    Returns:
        Adjusted position size in USD
    """
    # Confidence scaling
    conf_factor = max(0.5, min(1.5, confidence))
    
    # Volatility scaling (inverse)
    vol_factor = 1.0 / (1.0 + 5.0 * volatility)
    
    # Apply risk multiplier
    size = base_notional * conf_factor * vol_factor * risk_multiplier
    
    # Bounds
    return max(10.0, min(1000.0, size))

