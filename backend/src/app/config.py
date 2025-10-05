from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "configs"


def _read_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_users_config() -> Dict[str, Any]:
    return _read_yaml(CONFIG_DIR / "users.yaml")


def load_risk_config() -> Dict[str, Any]:
    return _read_yaml(CONFIG_DIR / "risk.yaml")


def load_symbols_config() -> Dict[str, Any]:
    return _read_yaml(CONFIG_DIR / "symbols.yaml")


def load_features_config() -> Dict[str, Any]:
    return _read_yaml(CONFIG_DIR / "features.yaml")


def load_model_config() -> Dict[str, Any]:
    return _read_yaml(CONFIG_DIR / "model.yaml")


