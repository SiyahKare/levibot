from __future__ import annotations

from backend.src.infra.version import (
    get_build_info,
    get_git_branch,
    get_git_sha,
    get_version,
)


def test_get_version_from_env(monkeypatch):
    monkeypatch.setenv("BUILD_VERSION", "1.2.0")
    assert get_version() == "1.2.0"


def test_get_version_default(monkeypatch):
    monkeypatch.delenv("BUILD_VERSION", raising=False)
    assert get_version() == "dev"


def test_get_git_sha_from_env(monkeypatch):
    monkeypatch.setenv("BUILD_SHA", "02f4b21abc123")
    assert get_git_sha() == "02f4b21"


def test_get_git_sha_from_git(monkeypatch):
    monkeypatch.setenv("BUILD_SHA", "local123")
    sha = get_git_sha()
    assert isinstance(sha, str)
    assert sha == "local123"[:7]


def test_get_git_branch_from_env(monkeypatch):
    monkeypatch.setenv("BUILD_BRANCH", "feature/test")
    assert get_git_branch() == "feature/test"


def test_get_build_info():
    info = get_build_info()
    assert "version" in info
    assert "git_sha" in info
    assert "branch" in info
    assert isinstance(info["version"], str)
    assert isinstance(info["git_sha"], str)
    assert isinstance(info["branch"], str)
