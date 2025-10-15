"""
Probability calibration for ML models.

Implements Platt scaling and Isotonic regression.
"""
from __future__ import annotations

import numpy as np


def calibrate_probabilities(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    method: str = "isotonic"
) -> tuple[np.ndarray, float]:
    """
    Calibrate probabilities using Platt scaling or Isotonic regression.

    Args:
        y_true: True labels (0/1)
        y_prob: Predicted probabilities (uncalibrated)
        method: "sigmoid" (Platt) or "isotonic"

    Returns:
        Tuple of (calibrated_probabilities, ECE_score)
    """
    from sklearn.isotonic import IsotonicRegression
    from sklearn.linear_model import LogisticRegression

    if method == "sigmoid":
        # Platt scaling
        calibrator = LogisticRegression()
        calibrator.fit(y_prob.reshape(-1, 1), y_true)
        y_calibrated = calibrator.predict_proba(y_prob.reshape(-1, 1))[:, 1]
    elif method == "isotonic":
        # Isotonic regression
        calibrator = IsotonicRegression(out_of_bounds="clip")
        y_calibrated = calibrator.fit_transform(y_prob, y_true)
    else:
        raise ValueError(f"Unknown calibration method: {method}")

    # Compute ECE (Expected Calibration Error)
    ece = expected_calibration_error(y_true, y_calibrated, n_bins=10)

    return y_calibrated, ece


def expected_calibration_error(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10
) -> float:
    """
    Compute Expected Calibration Error (ECE).

    ECE measures the difference between predicted probabilities and actual frequencies.

    Args:
        y_true: True labels (0/1)
        y_prob: Predicted probabilities
        n_bins: Number of bins for calibration curve

    Returns:
        ECE score (0 = perfect calibration, 1 = worst)
    """
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    bin_lowers = bin_boundaries[:-1]
    bin_uppers = bin_boundaries[1:]

    ece = 0.0
    for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
        # Find predictions in this bin
        in_bin = (y_prob > bin_lower) & (y_prob <= bin_upper)
        prop_in_bin = in_bin.mean()

        if prop_in_bin > 0:
            accuracy_in_bin = y_true[in_bin].mean()
            avg_confidence_in_bin = y_prob[in_bin].mean()
            ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin

    return float(ece)


def plot_calibration_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10,
    save_path: str | None = None
):
    """
    Plot calibration curve (reliability diagram).

    Args:
        y_true: True labels
        y_prob: Predicted probabilities
        n_bins: Number of bins
        save_path: Path to save plot (optional)
    """
    import matplotlib.pyplot as plt
    from sklearn.calibration import calibration_curve

    fraction_of_positives, mean_predicted_value = calibration_curve(
        y_true, y_prob, n_bins=n_bins, strategy="uniform"
    )

    plt.figure(figsize=(8, 6))
    plt.plot(mean_predicted_value, fraction_of_positives, "s-", label="Model")
    plt.plot([0, 1], [0, 1], "k--", label="Perfect calibration")
    plt.xlabel("Mean predicted probability")
    plt.ylabel("Fraction of positives")
    plt.title("Calibration Curve")
    plt.legend()
    plt.grid(alpha=0.3)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"📊 Calibration plot saved: {save_path}")
    else:
        plt.show()

    plt.close()

