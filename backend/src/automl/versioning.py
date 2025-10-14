"""
Model versioning and deployment module.

Manages model releases and symlink-based hot deployment.
"""

from __future__ import annotations

import os
from datetime import UTC
from pathlib import Path


def make_release_dir(base: str = "backend/data/models") -> Path:
    """
    Create a dated release directory for model artifacts.

    Uses RUN_DATE env var if set, otherwise current date.

    Args:
        base: Base models directory

    Returns:
        Path to release directory
    """
    run_date = os.environ.get("RUN_DATE", None)

    if not run_date:
        from datetime import datetime

        run_date = datetime.now(UTC).strftime("%Y-%m-%d")

    release_dir = Path(base) / run_date
    release_dir.mkdir(parents=True, exist_ok=True)

    return release_dir


def write_symlink(best_src: str, link_path: str) -> None:
    """
    Create/update symlink to best model.

    Hot deployment: engine will pick up new model on next load.

    Args:
        best_src: Source path of best model
        link_path: Target symlink path
    """
    link = Path(link_path)

    # Remove existing symlink/file
    if link.exists() or link.is_symlink():
        link.unlink()

    # Create symlink (relative for portability)
    src_path = Path(best_src).resolve()
    link.symlink_to(src_path)

    print(f"[Versioning] Symlink created: {link_path} -> {src_path}")


def list_releases(base: str = "backend/data/models") -> list[str]:
    """
    List all available model releases (by date).

    Args:
        base: Base models directory

    Returns:
        List of release dates (sorted, newest first)
    """
    base_path = Path(base)

    if not base_path.exists():
        return []

    releases = [
        d.name
        for d in base_path.iterdir()
        if d.is_dir() and d.name not in ("__pycache__",)
    ]

    # Filter to date-like directories (YYYY-MM-DD format)
    releases = [r for r in releases if len(r) == 10 and r[4] == "-" and r[7] == "-"]

    return sorted(releases, reverse=True)


def rollback_to_release(release_date: str, base: str = "backend/data/models") -> None:
    """
    Rollback to a specific release.

    Updates symlinks to point to models from that release.

    Args:
        release_date: Release date (e.g., "2025-10-13")
        base: Base models directory
    """
    release_dir = Path(base) / release_date

    if not release_dir.exists():
        raise FileNotFoundError(f"Release not found: {release_date}")

    # Find all model files in release
    lgbm_candidates = list(release_dir.rglob("lgbm.pkl"))
    tft_candidates = list(release_dir.rglob("tft.pt"))

    if lgbm_candidates:
        write_symlink(str(lgbm_candidates[0]), f"{base}/best_lgbm.pkl")

    if tft_candidates:
        write_symlink(str(tft_candidates[0]), f"{base}/best_tft.pt")

    print(f"[Rollback] Restored models from {release_date}")
