"""Purged walk-forward validation for genetic algorithm."""

import logging
from typing import Any

import numpy as np
import pandas as pd

from .fitness import train_and_score
from .label import create_walk_forward_splits

logger = logging.getLogger(__name__)


def purged_walk_forward(
    df: pd.DataFrame, chrom, n_folds: int = 5, embargo: int = 120
) -> float:
    """
    Perform purged walk-forward validation.

    Args:
        df: OHLCV DataFrame
        chrom: Chromosome with parameters
        n_folds: Number of folds
        embargo: Embargo period in samples

    Returns:
        Average fitness across folds
    """
    try:
        n = len(df)
        if n < 1000:
            logger.warning(f"Insufficient data for walk-forward: {n} samples")
            return -10.0

        # Create walk-forward splits
        train_indices, val_indices = create_walk_forward_splits(n, n_folds, embargo)

        fitness_scores = []

        for fold in range(n_folds):
            try:
                train_idx = train_indices[fold]
                val_idx = val_indices[fold]

                if len(train_idx) < 100 or len(val_idx) < 50:
                    logger.warning(f"Fold {fold}: Insufficient data")
                    continue

                # Get data for this fold
                train_df = df.iloc[train_idx].copy()
                val_df = df.iloc[val_idx].copy()

                # Train and score
                fitness, metrics = train_and_score(train_df, val_df, chrom)
                fitness_scores.append(fitness)

                logger.debug(
                    f"Fold {fold}: fitness={fitness:.4f}, "
                    f"sharpe={metrics.get('sharpe', 0):.4f}, "
                    f"dd={metrics.get('max_drawdown', 0):.4f}"
                )

            except Exception as e:
                logger.error(f"Error in fold {fold}: {e}")
                continue

        if not fitness_scores:
            logger.error("No valid folds completed")
            return -10.0

        avg_fitness = np.mean(fitness_scores)
        logger.info(
            f"Walk-forward completed: {len(fitness_scores)}/{n_folds} folds, "
            f"avg_fitness={avg_fitness:.4f}"
        )

        return float(avg_fitness)

    except Exception as e:
        logger.error(f"Error in purged_walk_forward: {e}")
        return -10.0


def time_series_split(
    df: pd.DataFrame, n_splits: int = 5
) -> list[tuple[np.ndarray, np.ndarray]]:
    """
    Create time series splits for validation.

    Args:
        df: DataFrame with time series data
        n_splits: Number of splits

    Returns:
        List of (train_indices, test_indices) tuples
    """
    n = len(df)
    split_size = n // n_splits

    splits = []
    for i in range(n_splits):
        test_start = i * split_size
        test_end = (i + 1) * split_size if i < n_splits - 1 else n

        train_indices = np.concatenate(
            [np.arange(0, test_start), np.arange(test_end, n)]
        )
        test_indices = np.arange(test_start, test_end)

        splits.append((train_indices, test_indices))

    return splits


def expanding_window_validation(
    df: pd.DataFrame, chrom, min_train_size: int = 1000, step_size: int = 500
) -> list[float]:
    """
    Perform expanding window validation.

    Args:
        df: OHLCV DataFrame
        chrom: Chromosome with parameters
        min_train_size: Minimum training size
        step_size: Step size for expanding window

    Returns:
        List of fitness scores
    """
    n = len(df)
    fitness_scores = []

    for start in range(min_train_size, n - 500, step_size):
        try:
            train_df = df.iloc[:start].copy()
            test_df = df.iloc[start : start + step_size].copy()

            if len(test_df) < 100:
                break

            fitness, metrics = train_and_score(train_df, test_df, chrom)
            fitness_scores.append(fitness)

            logger.debug(f"Expanding window {start}: fitness={fitness:.4f}")

        except Exception as e:
            logger.error(f"Error in expanding window {start}: {e}")
            continue

    return fitness_scores


def rolling_window_validation(
    df: pd.DataFrame, chrom, window_size: int = 1000, step_size: int = 500
) -> list[float]:
    """
    Perform rolling window validation.

    Args:
        df: OHLCV DataFrame
        chrom: Chromosome with parameters
        window_size: Training window size
        step_size: Step size for rolling window

    Returns:
        List of fitness scores
    """
    n = len(df)
    fitness_scores = []

    for start in range(0, n - window_size - 500, step_size):
        try:
            train_df = df.iloc[start : start + window_size].copy()
            test_df = df.iloc[start + window_size : start + window_size + 500].copy()

            if len(test_df) < 100:
                break

            fitness, metrics = train_and_score(train_df, test_df, chrom)
            fitness_scores.append(fitness)

            logger.debug(f"Rolling window {start}: fitness={fitness:.4f}")

        except Exception as e:
            logger.error(f"Error in rolling window {start}: {e}")
            continue

    return fitness_scores


def cross_validate_chromosome(
    df: pd.DataFrame, chrom, method: str = "purged_wf", **kwargs
) -> dict[str, Any]:
    """
    Cross-validate a chromosome using specified method.

    Args:
        df: OHLCV DataFrame
        chrom: Chromosome with parameters
        method: Validation method ("purged_wf", "expanding", "rolling")
        **kwargs: Additional parameters

    Returns:
        Dictionary with validation results
    """
    try:
        if method == "purged_wf":
            fitness = purged_walk_forward(df, chrom, **kwargs)
            return {"fitness": fitness, "method": method}

        elif method == "expanding":
            scores = expanding_window_validation(df, chrom, **kwargs)
            return {
                "fitness": np.mean(scores) if scores else -10.0,
                "scores": scores,
                "method": method,
            }

        elif method == "rolling":
            scores = rolling_window_validation(df, chrom, **kwargs)
            return {
                "fitness": np.mean(scores) if scores else -10.0,
                "scores": scores,
                "method": method,
            }

        else:
            raise ValueError(f"Unknown validation method: {method}")

    except Exception as e:
        logger.error(f"Error in cross_validate_chromosome: {e}")
        return {"fitness": -10.0, "error": str(e), "method": method}
