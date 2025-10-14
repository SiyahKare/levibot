"""
Nightly retraining pipeline orchestrator.

Runs end-to-end: data collection → features → training → versioning → deployment.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

from .build_features import build_features
from .collect_data import collect_ohlcv, save_raw
from .evaluate import load_score
from .train_lgbm import train_and_dump as train_lgbm
from .train_tft import train_and_dump as train_tft
from .versioning import make_release_dir, write_symlink

# Default symbols (override with SYMBOLS env var)
DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]


def main() -> None:
    """
    Main nightly retraining pipeline.

    Steps:
    1. Collect 24h OHLCV data for each symbol
    2. Build features + labels
    3. Train LGBM + TFT models
    4. Evaluate and pick best model
    5. Create symlinks for hot deployment
    """
    # Setup
    symbols_str = os.getenv("SYMBOLS", ",".join(DEFAULT_SYMBOLS))
    symbols = [s.strip() for s in symbols_str.split(",")]

    run_date = datetime.now(UTC).strftime("%Y-%m-%d")
    os.environ["RUN_DATE"] = run_date

    print(f"\n{'=' * 60}")
    print(f"🌙 Nightly AutoML Pipeline — {run_date}")
    print(f"{'=' * 60}")
    print(f"Symbols: {', '.join(symbols)}\n")

    # Create release directory
    release_dir = make_release_dir()
    print(f"📁 Release directory: {release_dir}\n")

    # Train models for each symbol
    results = []

    for symbol in symbols:
        print(f"🔄 Processing {symbol}...")

        # Step 1: Collect data
        print("  → Collecting 24h OHLCV data...")
        raw_data = collect_ohlcv(symbol, lookback_h=24)
        raw_path = save_raw(symbol, raw_data)
        print(f"     ✅ {len(raw_data)} candles saved to {raw_path}")

        # Step 2: Build features
        print("  → Building features...")
        features = build_features(raw_path, horizon=5)
        feat_path = Path(release_dir) / f"{symbol.replace('/', '-')}_features.json"
        feat_path.write_text(json.dumps(features, indent=2))
        print(f"     ✅ {len(features['X'])} samples, {len(features['X'][0])} features")

        # Step 3: Train models
        out_sym_dir = Path(release_dir) / symbol.replace("/", "-")
        out_sym_dir.mkdir(exist_ok=True)

        print("  → Training LGBM...")
        lgbm_path = train_lgbm(str(feat_path), str(out_sym_dir))

        print("  → Training TFT...")
        tft_path = train_tft(str(feat_path), str(out_sym_dir))

        # Step 4: Evaluate
        lgbm_score = load_score(lgbm_path)
        tft_score = load_score(tft_path)
        best_score = max(lgbm_score, tft_score)
        best_model = "LGBM" if lgbm_score >= tft_score else "TFT"

        print(
            f"  ✅ Best: {best_model} (score={best_score:.4f}) [LGBM={lgbm_score:.4f}, TFT={tft_score:.4f}]\n"
        )

        results.append(
            {
                "symbol": symbol,
                "lgbm_path": lgbm_path,
                "tft_path": tft_path,
                "lgbm_score": lgbm_score,
                "tft_score": tft_score,
                "best_score": best_score,
                "best_model": best_model,
            }
        )

    # Step 5: Pick global best model
    print(f"\n{'=' * 60}")
    print("🏆 Selecting global best model...")
    print(f"{'=' * 60}\n")

    global_best = max(results, key=lambda r: r["best_score"])

    # Save summary
    summary_path = Path(release_dir) / "summary.json"
    summary = {
        "run_date": run_date,
        "symbols": symbols,
        "results": results,
        "global_best": {
            "symbol": global_best["symbol"],
            "model": global_best["best_model"],
            "score": global_best["best_score"],
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"📊 Summary saved: {summary_path}")

    # Step 6: Create symlinks for hot deployment
    print("\n🔗 Creating deployment symlinks...")

    base_models_dir = "backend/data/models"

    # Use global best for both symlinks (simplification)
    if global_best["best_model"] == "LGBM":
        write_symlink(global_best["lgbm_path"], f"{base_models_dir}/best_lgbm.pkl")
        # Still link TFT even if it's not best (for ensemble)
        write_symlink(global_best["tft_path"], f"{base_models_dir}/best_tft.pt")
    else:
        write_symlink(global_best["tft_path"], f"{base_models_dir}/best_tft.pt")
        write_symlink(global_best["lgbm_path"], f"{base_models_dir}/best_lgbm.pkl")

    # Final summary
    print(f"\n{'=' * 60}")
    print("✅ Nightly AutoML Complete!")
    print(f"{'=' * 60}")
    print(f"🏆 Best: {global_best['symbol']} — {global_best['best_model']}")
    print(f"📈 Score: {global_best['best_score']:.4f}")
    print("🔗 Deployed: best_lgbm.pkl, best_tft.pt")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()

