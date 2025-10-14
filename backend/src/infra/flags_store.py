"""
Flags Store
Persistent flag management with atomic writes
"""

import json
import os
import shutil
import tempfile
import threading
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # fallback to JSON

FLAGS_PATH = os.getenv("FLAGS_PATH", "configs/flags.yaml")
_lock = threading.Lock()


def _ensure_dir(path: str) -> None:
    """Ensure directory exists for the given file path."""
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)


def load_flags() -> dict[str, Any]:
    """
    Load flags from persistent storage.

    Returns:
        Dictionary of flags, empty dict if file doesn't exist
    """
    if not os.path.exists(FLAGS_PATH):
        return {}

    try:
        with open(FLAGS_PATH) as f:
            content = f.read().strip()

        if not content:
            return {}

        # Try YAML first, fallback to JSON
        if yaml and FLAGS_PATH.endswith((".yaml", ".yml")):
            return yaml.safe_load(content) or {}
        else:
            return json.loads(content)

    except Exception as e:
        print(f"⚠️  Failed to load flags from {FLAGS_PATH}: {e}")
        return {}


def save_flags(flags: dict[str, Any]) -> str:
    """
    Save flags to persistent storage with atomic write.

    Args:
        flags: Dictionary of flags to save

    Returns:
        Path to saved file
    """
    _ensure_dir(FLAGS_PATH)

    with _lock:
        # Create temporary file in same directory for atomic move
        directory = os.path.dirname(FLAGS_PATH) or "."
        tmp_fd, tmp_path = tempfile.mkstemp(
            prefix="flags_", suffix=".tmp", dir=directory
        )

        try:
            with os.fdopen(tmp_fd, "w") as tmp_file:
                if yaml and FLAGS_PATH.endswith((".yaml", ".yml")):
                    # YAML format
                    tmp_file.write(yaml.safe_dump(flags, sort_keys=True))
                else:
                    # JSON format
                    tmp_file.write(json.dumps(flags, indent=2, sort_keys=True))

            # Atomic move (replaces old file)
            shutil.move(tmp_path, FLAGS_PATH)

        finally:
            # Clean up temp file if it still exists
            try:
                os.remove(tmp_path)
            except FileNotFoundError:
                pass

    return FLAGS_PATH


def merge_flags(updates: dict[str, Any]) -> dict[str, Any]:
    """
    Merge updates into existing flags and save.

    Args:
        updates: Dictionary of flag updates

    Returns:
        Merged flags dictionary
    """
    current = load_flags()
    current.update(updates)
    save_flags(current)
    return current
