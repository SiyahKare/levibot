from __future__ import annotations

import os
import subprocess


def get_version() -> str:
    """Return version from ENV or default."""
    return os.getenv("BUILD_VERSION", "dev")

def get_git_sha() -> str:
    """Return git SHA from ENV or try git command, fallback to 'unknown'."""
    sha = os.getenv("BUILD_SHA")
    if sha:
        value = sha.strip()
        return value[:7] if len(value) >= 7 else value
    
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short=7", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    
    return "unknown"

def get_git_branch() -> str:
    """Return git branch from ENV or try git command, fallback to 'unknown'."""
    branch = os.getenv("BUILD_BRANCH")
    if branch:
        return branch
    
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    
    return "unknown"

def get_build_info() -> dict[str, str]:
    """Return dict with version, git_sha, branch."""
    return {
        "version": get_version(),
        "git_sha": get_git_sha(),
        "branch": get_git_branch(),
    }
