"""
Symbol normalization across exchanges.
"""
from __future__ import annotations


def norm_symbol(raw_symbol: str, exchange: str = "mexc") -> str:
    """
    Normalize exchange-specific symbol format to standard format.
    
    Args:
        raw_symbol: Raw symbol from exchange (e.g., "BTC_USDT", "btcusdt")
        exchange: Exchange name
    
    Returns:
        Normalized symbol (e.g., "BTCUSDT")
    """
    if exchange.lower() == "mexc":
        # MEXC uses lowercase without separator: "btcusdt"
        return raw_symbol.replace("_", "").upper()
    
    # Default: uppercase and remove separators
    return raw_symbol.replace("_", "").replace("-", "").replace("/", "").upper()


def denorm_symbol(symbol: str, exchange: str = "mexc") -> str:
    """
    Convert normalized symbol back to exchange format.
    
    Args:
        symbol: Normalized symbol (e.g., "BTCUSDT")
        exchange: Exchange name
    
    Returns:
        Exchange-specific format (e.g., "btcusdt" for MEXC)
    """
    if exchange.lower() == "mexc":
        # MEXC WebSocket uses lowercase
        return symbol.lower()
    
    return symbol







