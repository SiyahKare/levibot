"""
Base Strategy Interface
"""
from typing import Literal, Protocol

Mode = Literal["paper", "real"]


class StrategyEngine(Protocol):
    """Base protocol for all trading strategies"""
    
    name: str
    
    def start(self, mode: Mode | None = None, overrides: dict | None = None) -> None:
        """Start the strategy engine"""
        ...
    
    def stop(self) -> None:
        """Stop the strategy engine"""
        ...
    
    def running(self) -> bool:
        """Check if engine is running"""
        ...
    
    def health(self) -> dict:
        """Get health status"""
        ...
    
    def params(self) -> dict:
        """Get current parameters"""
        ...
    
    def update_params(self, p: dict) -> dict:
        """Update parameters"""
        ...

