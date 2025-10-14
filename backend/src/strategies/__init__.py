"""
Strategy Registry
"""
from typing import Dict

from .base import StrategyEngine

# Global registry
REGISTRY: dict[str, StrategyEngine] = {}


def register(engine: StrategyEngine):
    """Register a strategy engine"""
    REGISTRY[engine.name] = engine


def get(name: str) -> StrategyEngine:
    """Get a registered strategy"""
    return REGISTRY[name]


def list_all() -> list:
    """List all registered strategies"""
    return [
        {"name": name, "health": engine.health()}
        for name, engine in REGISTRY.items()
    ]

