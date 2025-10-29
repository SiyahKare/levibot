"""Triple barrier labeling for time series data."""

import numpy as np
import pandas as pd


def triple_barrier(close: pd.Series, u_bps: int, d_bps: int, t_bars: int) -> pd.Series:
    """
    Generate triple barrier labels for time series.

    Args:
        close: Price series
        u_bps: Up barrier in basis points
        d_bps: Down barrier in basis points
        t_bars: Time barrier in bars

    Returns:
        Series with labels: 1 (up), -1 (down), 0 (timeout)
    """
    u = u_bps / 10000.0
    d = d_bps / 10000.0
    n = len(close)
    y = np.zeros(n)

    for i in range(n - t_bars):
        entry = close.iat[i]
        up = entry * (1 + u)
        dn = entry * (1 - d)

        # Look ahead window
        window = close.iloc[i + 1 : i + t_bars + 1]

        # Check which barrier is hit first
        hit_up = (window >= up).idxmax() if (window >= up).any() else None
        hit_dn = (window <= dn).idxmax() if (window <= dn).any() else None

        if hit_up and hit_dn:
            # Both barriers hit - choose the first one
            y[i] = 1 if hit_up < hit_dn else -1
        elif hit_up:
            y[i] = 1
        elif hit_dn:
            y[i] = -1
        else:
            # Timeout - no barrier hit
            y[i] = 0

    return pd.Series(y, index=close.index).fillna(0)


def embargo_indices(n: int, start: int, end: int, embargo: int) -> np.ndarray:
    """
    Create embargo mask for purged walk-forward validation.

    Args:
        n: Total length
        start: Validation start index
        end: Validation end index
        embargo: Embargo period in samples

    Returns:
        Array of indices to keep (excluding embargo region)
    """
    left = max(0, start - embargo)
    right = min(n, end + embargo)
    return np.r_[0:left, right:n]


def purge_embargo_mask(
    n: int, validation_starts: list, validation_ends: list, embargo: int
) -> np.ndarray:
    """
    Create mask for multiple validation periods with embargo.

    Args:
        n: Total length
        validation_starts: List of validation start indices
        validation_ends: List of validation end indices
        embargo: Embargo period in samples

    Returns:
        Boolean mask: True for training samples, False for embargo
    """
    mask = np.ones(n, dtype=bool)

    for start, end in zip(validation_starts, validation_ends):
        left = max(0, start - embargo)
        right = min(n, end + embargo)
        mask[left:right] = False

    return mask


def create_walk_forward_splits(
    n: int, n_folds: int = 5, embargo: int = 120
) -> tuple[list, list]:
    """
    Create purged walk-forward validation splits.

    Args:
        n: Total length
        n_folds: Number of folds
        embargo: Embargo period in samples

    Returns:
        Tuple of (train_indices_list, validation_indices_list)
    """
    fold_size = n // n_folds
    train_indices = []
    val_indices = []

    for k in range(n_folds):
        val_start = k * fold_size
        val_end = (k + 1) * fold_size if k < n_folds - 1 else n

        # Create embargo mask
        mask = purge_embargo_mask(n, [val_start], [val_end], embargo)

        # Get training indices (excluding embargo)
        train_idx = np.where(mask)[0]
        val_idx = np.arange(val_start, val_end)

        train_indices.append(train_idx)
        val_indices.append(val_idx)

    return train_indices, val_indices


def calculate_label_stats(labels: pd.Series) -> dict:
    """Calculate statistics for label distribution."""
    total = len(labels)
    up_count = (labels == 1).sum()
    down_count = (labels == -1).sum()
    timeout_count = (labels == 0).sum()

    return {
        "total": total,
        "up_pct": up_count / total * 100,
        "down_pct": down_count / total * 100,
        "timeout_pct": timeout_count / total * 100,
        "up_count": up_count,
        "down_count": down_count,
        "timeout_count": timeout_count,
    }
