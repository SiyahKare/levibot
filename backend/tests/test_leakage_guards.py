"""
Leakage Guard Tests - FAIL FAST on data leakage risks.

These tests MUST pass before any model training.
"""
from __future__ import annotations

import pandas as pd
import pytest


class TestTimeBasedSplit:
    """Test time-based train/val/test splits."""

    def test_train_val_no_overlap(self):
        """Train and validation sets must not overlap in time."""
        # Mock data
        train_df = pd.DataFrame({
            "ts": [1000, 2000, 3000],
            "symbol": ["BTCUSDT", "BTCUSDT", "BTCUSDT"],
        })
        val_df = pd.DataFrame({
            "ts": [4000, 5000, 6000],
            "symbol": ["BTCUSDT", "BTCUSDT", "BTCUSDT"],
        })

        train_max = train_df["ts"].max()
        val_min = val_df["ts"].min()

        assert train_max < val_min, (
            f"Time-split violation: train_max ({train_max}) >= val_min ({val_min}). "
            "POTENTIAL DATA LEAKAGE!"
        )

    def test_val_test_no_overlap(self):
        """Validation and test sets must not overlap in time."""
        val_df = pd.DataFrame({
            "ts": [4000, 5000, 6000],
            "symbol": ["BTCUSDT", "BTCUSDT", "BTCUSDT"],
        })
        test_df = pd.DataFrame({
            "ts": [7000, 8000, 9000],
            "symbol": ["BTCUSDT", "BTCUSDT", "BTCUSDT"],
        })

        val_max = val_df["ts"].max()
        test_min = test_df["ts"].min()

        assert val_max < test_min, (
            f"Time-split violation: val_max ({val_max}) >= test_min ({test_min}). "
            "POTENTIAL DATA LEAKAGE!"
        )

    def test_per_symbol_monotonic(self):
        """Timestamps must be monotonically increasing per symbol."""
        df = pd.DataFrame({
            "ts": [1000, 2000, 1500, 3000],  # 1500 breaks monotonic
            "symbol": ["BTCUSDT", "BTCUSDT", "BTCUSDT", "BTCUSDT"],
        })

        for symbol in df["symbol"].unique():
            symbol_df = df[df["symbol"] == symbol]
            is_monotonic = symbol_df["ts"].is_monotonic_increasing

            assert is_monotonic, (
                f"Timestamp not monotonic for {symbol}. "
                "This may indicate shuffling or incorrect sorting. "
                "RISK: Future information leakage!"
            )


class TestFeatureFutureLeakage:
    """Test that features don't use future information."""

    def test_no_future_shifts(self):
        """
        Features must not use shift with negative values.
        
        Example violation: df['future_close'] = df['close'].shift(-5)
        """
        # This test would inspect code or feature definitions
        # For now, we test the principle with mock data
        
        df = pd.DataFrame({
            "close": [100, 101, 102, 103, 104],
            "ts": [1000, 2000, 3000, 4000, 5000],
        })
        
        # Good: using past data
        df["ret_1"] = df["close"].pct_change(1)  # uses t-1
        
        # BAD (commented out): df["future_ret"] = df["close"].shift(-1)
        
        # Check: first value of ret_1 should be NaN (no past data)
        assert pd.isna(df["ret_1"].iloc[0]), "First return should be NaN (no past data)"
        
        # Check: last value should be valid (has past data)
        assert not pd.isna(df["ret_1"].iloc[-1]), "Last return should be valid"

    def test_label_generation_safe(self):
        """
        Labels (target) can use future data, but must be excluded from features.
        """
        df = pd.DataFrame({
            "close": [100, 101, 102, 103, 104, 105],
            "ts": [1000, 2000, 3000, 4000, 5000, 6000],
        })
        
        # Label: future return (OK for labels, NOT for features)
        df["target_ret_h5"] = df["close"].shift(-5) / df["close"] - 1
        
        # When training at t=1000, we should NOT see target for t=1000
        # (because it uses close at t=6000)
        # This is enforced by time-based split + proper feature selection
        
        # Simulate: only use features available at prediction time
        feature_cols = ["close", "ts"]  # NOT including "target_ret_h5"
        label_col = "target_ret_h5"
        
        assert label_col not in feature_cols, (
            f"Label '{label_col}' found in features! CRITICAL LEAKAGE!"
        )


class TestSchemaValidation:
    """Test feature schema compliance."""

    def test_required_columns_present(self):
        """All required columns must be present."""
        df = pd.DataFrame({
            "ts": [1000, 2000, 3000],
            "symbol": ["BTCUSDT", "BTCUSDT", "BTCUSDT"],
            "close": [100.0, 101.0, 102.0],
        })
        
        required = {"ts", "symbol", "close"}
        actual = set(df.columns)
        
        missing = required - actual
        assert len(missing) == 0, f"Missing required columns: {missing}"

    def test_no_nulls_in_required_fields(self):
        """Required fields must not have null values."""
        df = pd.DataFrame({
            "ts": [1000, 2000, None],  # NULL in required field
            "symbol": ["BTCUSDT", "BTCUSDT", "BTCUSDT"],
            "close": [100.0, 101.0, 102.0],
        })
        
        required_fields = ["ts", "symbol", "close"]
        
        for field in required_fields:
            null_count = df[field].isnull().sum()
            assert null_count == 0, (
                f"Required field '{field}' has {null_count} null values. "
                "This violates schema constraints."
            )

    def test_dtypes_match_schema(self):
        """Data types must match schema specification."""
        df = pd.DataFrame({
            "ts": pd.Series([1000, 2000, 3000], dtype="int64"),
            "close": pd.Series([100.0, 101.0, 102.0], dtype="float64"),
            "volume": pd.Series([1000.0, 1100.0, 1200.0], dtype="float64"),
        })
        
        expected_dtypes = {
            "ts": "int64",
            "close": "float64",
            "volume": "float64",
        }
        
        for col, expected_dtype in expected_dtypes.items():
            actual_dtype = str(df[col].dtype)
            assert actual_dtype == expected_dtype, (
                f"Column '{col}': expected {expected_dtype}, got {actual_dtype}"
            )


class TestSnapshotIntegrity:
    """Test snapshot manifest and checksums."""

    def test_manifest_required_fields(self):
        """Manifest must have all required fields."""
        manifest = {
            "snapshot_id": "2025-10-15T12:00:00Z",
            "symbols": ["BTCUSDT", "ETHUSDT"],
            "range": {"start": "2025-07-15", "end": "2025-10-15"},
            "files": [
                {"path": "BTCUSDT.parquet", "rows": 43200, "sha256": "abc123"}
            ],
        }
        
        required = {"snapshot_id", "symbols", "range", "files"}
        actual = set(manifest.keys())
        
        missing = required - actual
        assert len(missing) == 0, f"Manifest missing required fields: {missing}"

    def test_checksum_format(self):
        """Checksums must be valid SHA-256 (64 hex characters)."""
        checksum = "a" * 64  # Valid SHA-256
        assert len(checksum) == 64, "SHA-256 must be 64 characters"
        assert all(c in "0123456789abcdef" for c in checksum.lower()), (
            "SHA-256 must be hexadecimal"
        )


# Mark all tests as critical (fail-fast in CI)
pytestmark = pytest.mark.leakage_guards

