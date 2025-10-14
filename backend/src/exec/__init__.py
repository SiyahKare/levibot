"""
Executor registry for exchange integrations.
"""
import os
from typing import Any

from .mexc_ccxt import create_mexc_executor

_EXECUTOR: Any | None = None


def get_executor() -> Any | None:
    """
    Get the configured executor (MEXC or None for paper mode).
    
    Returns:
        - MexcExecutor instance if EXCHANGE=MEXC
        - None if paper mode or no exchange configured
    """
    global _EXECUTOR
    
    if _EXECUTOR is not None:
        return _EXECUTOR
    
    exchange = os.getenv("EXCHANGE", "").upper()
    
    if exchange == "MEXC":
        _EXECUTOR = create_mexc_executor()
    
    return _EXECUTOR

