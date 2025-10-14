"""Tests for gap filler utility."""

from src.data.gap_filler import fill_minute_bars


def test_fill_bars_inserts_missing_minutes():
    """Test that gap filler inserts synthetic bars for missing minutes."""
    base = 1_700_000_000_000
    # 3-minute gap between bars
    ohlcv = [
        [base, 1, 2, 0.5, 1.5, 10],
        [base + 3 * 60_000, 1.6, 2, 1.2, 1.8, 12],
    ]
    out = fill_minute_bars(ohlcv)

    # Should have: base, +1m (synthetic), +2m (synthetic), +3m
    assert len(out) == 4
    assert out[1][0] == base + 60_000
    assert out[2][0] == base + 2 * 60_000
    assert out[1][4] == 1.5  # Forward-fill from last close
    assert out[2][4] == 1.5
    assert out[1][5] == 0.0  # Zero volume


def test_no_gaps_returns_original():
    """Test that bars without gaps are returned unchanged."""
    base = 1_700_000_000_000
    ohlcv = [
        [base, 1, 2, 0.5, 1.5, 10],
        [base + 60_000, 1.5, 2, 1.2, 1.6, 12],
        [base + 120_000, 1.6, 2, 1.4, 1.8, 15],
    ]
    out = fill_minute_bars(ohlcv)

    assert len(out) == 3
    assert out == ohlcv


def test_empty_list_returns_empty():
    """Test that empty input returns empty output."""
    assert fill_minute_bars([]) == []

