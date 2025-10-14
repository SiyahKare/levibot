"""
Shadow Trading & Canary Deployment

Log predictions and trades without executing, for A/B testing and validation.
"""
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Any


class ShadowLogger:
    """Logs shadow trades for performance comparison."""
    
    def __init__(self, log_dir: str = "backend/data/logs/shadow"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def log_prediction(
        self,
        model: str,
        symbol: str,
        prediction: dict[str, Any],
        actual_return: float | None = None,
    ) -> None:
        """Log a prediction for later analysis."""
        log_file = self.log_dir / f"predictions_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "symbol": symbol,
            "prediction": prediction,
            "actual_return": actual_return,
        }
        
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def log_trade(
        self,
        model: str,
        symbol: str,
        side: str,
        entry_price: float,
        exit_price: float | None = None,
        pnl: float | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Log a shadow trade."""
        log_file = self.log_dir / f"trades_{datetime.now().strftime('%Y%m%d')}.jsonl"
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "symbol": symbol,
            "side": side,
            "entry_price": entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "return": pnl / entry_price if (pnl and entry_price) else None,
            "metadata": metadata or {},
        }
        
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")


class CanaryDeployment:
    """Manages canary deployment of new models."""
    
    def __init__(self, config_path: str = "backend/data/registry/canary_policy.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.shadow_logger = ShadowLogger()
    
    def _load_config(self) -> dict:
        """Load canary configuration."""
        if not self.config_path.exists():
            return {
                "enabled": False,
                "fraction": 0.1,
                "min_confidence": 0.55,
            }
        
        with open(self.config_path) as f:
            return json.load(f)
    
    def should_use_canary(self) -> bool:
        """Decide if this prediction should use canary model."""
        if not self.config.get("enabled", False):
            return False
        
        fraction = self.config.get("fraction", 0.1)
        return random.random() < fraction
    
    def is_guard_passed(self, staleness_sec: float, ece: float, sharpe: float) -> bool:
        """Check if guards are satisfied."""
        guards = self.config.get("guards", {})
        
        if staleness_sec > guards.get("max_staleness_sec", 1800):
            return False
        
        if ece > guards.get("max_ece", 0.06):
            return False
        
        if sharpe < guards.get("min_sharpe", 0.8):
            return False
        
        return True
    
    def log_canary_prediction(
        self,
        symbol: str,
        prediction: dict,
        used_canary: bool,
    ) -> None:
        """Log canary prediction."""
        self.shadow_logger.log_prediction(
            model="canary" if used_canary else "prod",
            symbol=symbol,
            prediction=prediction,
        )


# Global instances
_shadow_logger = ShadowLogger()
_canary_deployment = CanaryDeployment()


def get_shadow_logger() -> ShadowLogger:
    """Get global shadow logger instance."""
    return _shadow_logger


def get_canary_deployment() -> CanaryDeployment:
    """Get global canary deployment instance."""
    return _canary_deployment

