#!/usr/bin/env python3
"""
Model Promotion Script

Promote a trained model to "current" in the registry.

Usage:
    python promote_model.py <model_path> [notes]
"""
import json
import sys
from pathlib import Path


def promote_model(model_path: str, notes: str = ""):
    """
    Promote a model to current in the registry.
    
    Args:
        model_path: Path to the model file
        notes: Optional promotion notes
    """
    registry_path = Path("backend/data/registry/model_registry.json")
    
    if not registry_path.exists():
        print(f"❌ Registry not found: {registry_path}")
        sys.exit(1)
    
    if not Path(model_path).exists():
        print(f"❌ Model file not found: {model_path}")
        sys.exit(1)
    
    # Load registry
    with open(registry_path) as f:
        registry = json.load(f)
    
    current = registry.get("current")
    if not current:
        print("❌ No current model in registry")
        sys.exit(1)
    
    # Archive old model if exists
    if "path" in current:
        old_path = current["path"]
        if "archive" not in registry:
            registry["archive"] = []
        
        archive_entry = current.copy()
        archive_entry["archived_at"] = Path(model_path).stem.split("_")[-1]  # timestamp from filename
        archive_entry["notes"] = notes
        registry["archive"].append(archive_entry)
    
    # Update current
    current["path"] = model_path
    current["promoted_at"] = Path(model_path).stem.split("_")[-1]
    if notes:
        current["notes"] = notes
    
    registry["current"] = current
    
    # Save
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)
    
    print(f"✅ Model promoted: {model_path}")
    print(f"   Registry: {registry_path}")
    if notes:
        print(f"   Notes: {notes}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python promote_model.py <model_path> [notes]")
        sys.exit(1)
    
    model_path = sys.argv[1]
    notes = sys.argv[2] if len(sys.argv) > 2 else ""
    
    promote_model(model_path, notes)


if __name__ == "__main__":
    main()

