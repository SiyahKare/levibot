"""
Tests for nightly AutoML pipeline.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from src.automl.build_features import build_features
from src.automl.collect_data import collect_ohlcv, save_raw
from src.automl.evaluate import calculate_sharpe, load_score
from src.automl.train_lgbm import train_and_dump as train_lgbm
from src.automl.train_tft import train_and_dump as train_tft
from src.automl.versioning import list_releases, make_release_dir, write_symlink


def test_collect_ohlcv():
    """Test OHLCV data collection."""
    data = collect_ohlcv("BTCUSDT", lookback_h=1)
    assert len(data) == 60  # 1 hour = 60 x 1-min bars
    assert all(k in data[0] for k in ["ts", "open", "high", "low", "close", "volume"])


def test_save_raw(tmp_path, monkeypatch):
    """Test raw data persistence."""
    monkeypatch.chdir(tmp_path)
    os.makedirs("backend/data/raw", exist_ok=True)

    data = collect_ohlcv("ETHUSDT", lookback_h=1)
    path = save_raw("ETHUSDT", data)

    assert Path(path).exists()
    loaded = json.loads(Path(path).read_text())
    assert len(loaded) == len(data)


def test_build_features(tmp_path, monkeypatch):
    """Test feature engineering."""
    monkeypatch.chdir(tmp_path)
    os.makedirs("backend/data/raw", exist_ok=True)

    # Create raw data
    data = collect_ohlcv("BTCUSDT", lookback_h=2)
    raw_path = save_raw("BTCUSDT", data)

    # Build features
    features = build_features(raw_path, horizon=5)

    assert "X" in features
    assert "y" in features
    assert len(features["X"]) == len(features["y"])
    assert len(features["X"]) == len(data)

    # Check feature keys
    sample = features["X"][0]
    expected_keys = [
        "close",
        "ret1",
        "ret5",
        "sma20_gap",
        "sma50_gap",
        "ema12_gap",
        "ema26_gap",
        "volume",
        "volatility",
    ]
    assert all(k in sample for k in expected_keys)


def test_train_lgbm(tmp_path, monkeypatch):
    """Test LGBM training."""
    monkeypatch.chdir(tmp_path)
    os.makedirs("backend/data/raw", exist_ok=True)

    # Prepare data
    data = collect_ohlcv("BTCUSDT", lookback_h=2)
    raw_path = save_raw("BTCUSDT", data)
    features = build_features(raw_path, horizon=5)

    feat_path = Path("features.json")
    feat_path.write_text(json.dumps(features))

    # Train
    model_path = train_lgbm(str(feat_path), "models", n_trials=8)

    assert Path(model_path).exists()

    # Load and check metadata
    meta = json.loads(Path(model_path).read_text())
    assert meta["type"] == "lgbm_mock"
    assert "score" in meta
    assert "params" in meta


def test_train_tft(tmp_path, monkeypatch):
    """Test TFT training."""
    monkeypatch.chdir(tmp_path)

    # Prepare minimal feature data
    features = {"X": [{"close": 100}] * 100, "y": [0, 1] * 50}
    feat_path = Path("features.json")
    feat_path.write_text(json.dumps(features))

    # Train
    model_path = train_tft(str(feat_path), "models")

    assert Path(model_path).exists()

    meta = json.loads(Path(model_path).read_text())
    assert meta["type"] == "tft_mock"
    assert "score" in meta


def test_load_score(tmp_path, monkeypatch):
    """Test model score loading."""
    monkeypatch.chdir(tmp_path)

    # Create mock model
    model_path = Path("model.pkl")
    model_path.write_text(json.dumps({"score": 0.75}))

    score = load_score(str(model_path))
    assert score == 0.75

    # Non-existent model
    score = load_score("nonexistent.pkl")
    assert score == 0.0


def test_calculate_sharpe():
    """Test Sharpe ratio calculation."""
    # Positive returns
    returns = [0.01, 0.02, 0.01, 0.03, -0.01, 0.02]
    sharpe = calculate_sharpe(returns)
    assert sharpe > 0

    # Negative returns
    returns = [-0.01, -0.02, -0.01]
    sharpe = calculate_sharpe(returns)
    assert sharpe < 0

    # Zero returns
    returns = [0.0, 0.0, 0.0]
    sharpe = calculate_sharpe(returns)
    assert sharpe == 0.0


def test_make_release_dir(tmp_path, monkeypatch):
    """Test release directory creation."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("RUN_DATE", "2025-10-15")

    release_dir = make_release_dir("models")

    assert release_dir.exists()
    assert "2025-10-15" in str(release_dir)


def test_write_symlink(tmp_path, monkeypatch):
    """Test symlink creation."""
    monkeypatch.chdir(tmp_path)

    # Create source file
    src = Path("model_v1.pkl")
    src.write_text("model data")

    # Create symlink
    link = Path("best_model.pkl")
    write_symlink(str(src), str(link))

    assert link.is_symlink()
    assert link.resolve() == src.resolve()

    # Update symlink
    src2 = Path("model_v2.pkl")
    src2.write_text("updated model")
    write_symlink(str(src2), str(link))

    assert link.resolve() == src2.resolve()


def test_list_releases(tmp_path, monkeypatch):
    """Test release listing."""
    monkeypatch.chdir(tmp_path)

    base = Path("models")
    base.mkdir()

    # Create date-like directories
    (base / "2025-10-13").mkdir()
    (base / "2025-10-14").mkdir()
    (base / "2025-10-15").mkdir()
    (base / "__pycache__").mkdir()  # should be ignored

    releases = list_releases(str(base))

    assert len(releases) == 3
    assert releases[0] == "2025-10-15"  # newest first
    assert releases[-1] == "2025-10-13"
    assert "__pycache__" not in releases


@pytest.mark.slow
def test_nightly_pipeline_smoke(tmp_path, monkeypatch):
    """
    Full integration test: run nightly pipeline end-to-end.

    Marked as slow (use -m "not slow" to skip).
    """
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("RUN_DATE", "2025-10-15")
    monkeypatch.setenv("SYMBOLS", "BTCUSDT,ETHUSDT")

    os.makedirs("backend/data/models", exist_ok=True)
    os.makedirs("backend/data/raw", exist_ok=True)

    from src.automl.nightly_retrain import main

    # Run pipeline
    main()

    # Verify outputs (use RUN_DATE env var, not hardcoded date)
    run_date = os.environ.get("RUN_DATE", "2025-10-15")
    assert Path(f"backend/data/models/{run_date}").exists()
    assert Path(f"backend/data/models/{run_date}/summary.json").exists()
    assert Path("backend/data/models/best_lgbm.pkl").is_symlink()
    assert Path("backend/data/models/best_tft.pt").is_symlink()

    # Check summary
    summary = json.loads(
        Path(f"backend/data/models/{run_date}/summary.json").read_text()
    )
    assert summary["run_date"] == run_date
    assert len(summary["results"]) == 2  # BTCUSDT, ETHUSDT
    assert "global_best" in summary
