"""
Strategy Registry
Central registration and management for all trading strategies
"""
from typing import Any

from .base.interface import StrategyEngine

# Global strategy registry
REGISTRY: dict[str, StrategyEngine] = {}


def register(engine: StrategyEngine) -> None:
    """
    Register a strategy engine.
    
    Args:
        engine: Strategy engine instance
    """
    REGISTRY[engine.name] = engine


def get(name: str) -> StrategyEngine | None:
    """
    Get a registered strategy engine.
    
    Args:
        name: Strategy name
    
    Returns:
        Strategy engine or None if not found
    """
    return REGISTRY.get(name)


def list_strategies() -> list[dict[str, Any]]:
    """
    List all registered strategies.
    
    Returns:
        List of strategy info dicts
    """
    return [
        {
            "name": name,
            "health": engine.health()
        }
        for name, engine in REGISTRY.items()
    ]

