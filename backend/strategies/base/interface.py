"""
Base Strategy Interface
Common protocol for all trading strategies
"""
from typing import Any, Literal, Protocol


class StrategyEngine(Protocol):
    """
    Common interface for all trading strategy engines.
    
    All strategies (LSE, Daytrade, Swing) must implement this protocol.
    """
    
    name: str
    
    def start(
        self,
        mode: Literal["paper", "real"] = "paper",
        overrides: dict[str, Any] | None = None
    ) -> None:
        """
        Start the strategy engine.
        
        Args:
            mode: Trading mode (paper or real)
            overrides: Optional parameter overrides
        """
        ...
    
    def stop(self) -> None:
        """Stop the strategy engine."""
        ...
    
    def health(self) -> dict[str, Any]:
        """
        Get strategy health status.
        
        Returns:
            Health metrics including:
            - running: bool
            - mode: str
            - guards: dict
            - latency_ms: float
            - ws_ok: bool
        """
        ...
    
    def params(self) -> dict[str, Any]:
        """
        Get current strategy parameters.
        
        Returns:
            Current parameter configuration
        """
        ...
    
    def update_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """
        Update strategy parameters.
        
        Args:
            params: New parameter values
        
        Returns:
            Updated parameters
        """
        ...

