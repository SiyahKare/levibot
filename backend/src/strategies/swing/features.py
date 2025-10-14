"""
Swing Trading Features - Technical Indicators
Reuses Day trading indicators with longer periods
"""

from ..day.features import (
    DayFeatureCache,
    calculate_adx,
    calculate_donchian_channels,
    calculate_ema,
    calculate_rsi,
)

# Re-export all functions
__all__ = [
    "calculate_ema",
    "calculate_rsi",
    "calculate_donchian_channels",
    "calculate_adx",
    "DayFeatureCache",  # Can be reused for swing with longer TTL
]


# Swing-specific aliases
SwingFeatureCache = DayFeatureCache  # Same structure, different TTL usage
