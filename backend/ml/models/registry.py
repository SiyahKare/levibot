"""
Model Registry

Version management and metadata for ML models.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class ModelRegistry:
    """
    Model registry for version control and metadata.
    
    Features:
    - Track model versions
    - Store metrics and metadata
    - Promote models (canary -> prod)
    - Rollback support
    """
    
    def __init__(self, registry_path: str = "backend/data/registry/model_registry.json"):
        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.data = self._load()
    
    def _load(self) -> dict:
        """Load registry from disk."""
        if self.registry_path.exists():
            with open(self.registry_path) as f:
                return json.load(f)
        return {"current": {}, "history": []}
    
    def _save(self):
        """Save registry to disk."""
        with open(self.registry_path, "w") as f:
            json.dump(self.data, f, indent=2)
    
    def register_model(
        self,
        model_path: str,
        symbol: str,
        timeframe: str,
        metrics: dict,
        features: list[str],
        metadata: dict | None = None,
    ) -> str:
        """
        Register a new model.
        
        Args:
            model_path: Path to model file
            symbol: Trading symbol
            timeframe: Timeframe
            metrics: Model metrics
            features: Feature list
            metadata: Additional metadata
        
        Returns:
            Model ID
        """
        model_id = f"{symbol}_{timeframe}_{int(datetime.now().timestamp())}"
        
        model_entry = {
            "id": model_id,
            "symbol_set": [symbol],
            "timeframe": timeframe,
            "path": model_path,
            "metrics": metrics,
            "features": features,
            "registered_at": datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        
        # Add to history
        if "history" not in self.data:
            self.data["history"] = []
        
        self.data["history"].append(model_entry)
        
        # Limit history size
        if len(self.data["history"]) > 20:
            self.data["history"] = self.data["history"][-20:]
        
        self._save()
        
        return model_id
    
    def promote_to_current(self, model_id: str):
        """Promote a model to production (current)."""
        # Find model in history
        model = None
        for entry in self.data.get("history", []):
            if entry["id"] == model_id:
                model = entry
                break
        
        if model is None:
            raise ValueError(f"Model {model_id} not found in history")
        
        # Backup current
        if "current" in self.data and self.data["current"]:
            self.data["previous"] = self.data["current"]
        
        # Promote
        self.data["current"] = model
        self._save()
        
        print(f"✅ Promoted {model_id} to current")
    
    def rollback(self):
        """Rollback to previous model."""
        if "previous" not in self.data or not self.data["previous"]:
            raise ValueError("No previous model to rollback to")
        
        self.data["current"] = self.data["previous"]
        self.data["previous"] = {}
        self._save()
        
        print("⏮️  Rolled back to previous model")
    
    def get_current(self) -> dict | None:
        """Get current production model."""
        return self.data.get("current")
    
    def get_history(self, limit: int = 10) -> list[dict]:
        """Get model history."""
        history = self.data.get("history", [])
        return history[-limit:]
    
    def get_stats(self) -> dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_models": len(self.data.get("history", [])),
            "current_model": self.data.get("current", {}).get("id"),
            "current_metrics": self.data.get("current", {}).get("metrics"),
            "registry_path": str(self.registry_path),
        }
    
    def compare_models(self, model_id_1: str, model_id_2: str) -> dict:
        """Compare two models."""
        models = {}
        for entry in self.data.get("history", []):
            if entry["id"] in [model_id_1, model_id_2]:
                models[entry["id"]] = entry
        
        if len(models) != 2:
            raise ValueError("One or both models not found")
        
        return {
            "model_1": models[model_id_1],
            "model_2": models[model_id_2],
            "metrics_diff": {
                k: models[model_id_2]["metrics"].get(k, 0) - models[model_id_1]["metrics"].get(k, 0)
                for k in models[model_id_1]["metrics"].keys()
            },
        }


# Global instance
_REGISTRY: ModelRegistry | None = None


def get_model_registry() -> ModelRegistry:
    """Get or create global model registry."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ModelRegistry()
    return _REGISTRY

