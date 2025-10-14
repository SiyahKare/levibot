"""
Risk policy configuration loader.
"""

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class RiskPolicy:
    """
    Risk management policy configuration.

    Attributes:
        max_daily_loss_pct: Maximum daily loss percentage (e.g., 3.0 = 3%)
        max_symbol_risk_pct: Maximum risk per symbol as fraction of equity (e.g., 0.20 = 20%)
        kelly_fraction: Kelly criterion fraction (e.g., 0.25 = quarter Kelly)
        vol_target_ann: Target annual volatility (e.g., 0.15 = 15%)
        max_concurrent_positions: Maximum number of concurrent positions
        rebalance: Rebalance frequency ("daily", "weekly", "monthly")
    """

    max_daily_loss_pct: float = 3.0
    max_symbol_risk_pct: float = 0.20
    kelly_fraction: float = 0.25
    vol_target_ann: float = 0.15
    max_concurrent_positions: int = 5
    rebalance: str = "weekly"


def load_policy(path: str = "config/risk_policy.yaml") -> RiskPolicy:
    """
    Load risk policy from YAML file.

    Falls back to defaults if file doesn't exist.

    Args:
        path: Path to YAML config file

    Returns:
        RiskPolicy instance
    """
    policy_path = Path(path)

    if not policy_path.exists():
        print(f"⚠️ Risk policy not found at {path}, using defaults")
        return RiskPolicy()

    try:
        data = yaml.safe_load(policy_path.read_text()) or {}

        # Build kwargs from dataclass fields
        kwargs = {}
        for field_name in RiskPolicy.__annotations__.keys():
            if field_name in data:
                kwargs[field_name] = data[field_name]

        policy = RiskPolicy(**kwargs)
        print(f"✅ Loaded risk policy from {path}")
        return policy

    except Exception as e:
        print(f"⚠️ Error loading risk policy: {e}, using defaults")
        return RiskPolicy()
