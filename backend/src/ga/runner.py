"""GA runner for CLI and orchestration."""

import json
import logging
import time
from pathlib import Path
from typing import Any

from .features_adapter import load_panel
from .ga_core import evolve
from .genes import Chromosome

logger = logging.getLogger(__name__)


def run_ga(
    symbol: str = "BTC/USDT",
    timeframe: str = "1m",
    days: int = 180,
    pop_size: int = 36,
    gens: int = 15,
    n_folds: int = 6,
    embargo: int = 120,
    outdir: str = "backend/data/ga",
    n_jobs: int = 1,
) -> dict[str, Any]:
    """
    Run genetic algorithm optimization.

    Args:
        symbol: Trading symbol
        timeframe: Data timeframe
        days: Number of days to load
        pop_size: Population size
        gens: Number of generations
        n_folds: Number of folds for validation
        embargo: Embargo period
        outdir: Output directory
        n_jobs: Number of parallel jobs

    Returns:
        Dictionary with results
    """
    logger.info(f"Starting GA optimization for {symbol}")
    logger.info(
        f"Parameters: timeframe={timeframe}, days={days}, "
        f"pop_size={pop_size}, gens={gens}, n_folds={n_folds}"
    )

    try:
        # Load data
        logger.info("Loading market data...")
        dfs = load_panel([symbol], timeframe, days)
        df = dfs.get(symbol)

        if df is None or df.empty:
            raise RuntimeError(f"No data available for {symbol}")

        logger.info(f"Loaded {len(df)} bars for {symbol}")

        # Check data quality
        if len(df) < 1000:
            logger.warning(
                f"Limited data: {len(df)} bars. Consider increasing days parameter."
            )

        # Run evolution
        logger.info("Starting evolution...")
        start_time = time.time()

        best_chrom, best_fitness, history = evolve(
            df=df,
            pop_size=pop_size,
            gens=gens,
            elite_frac=0.3,
            n_folds=n_folds,
            embargo=embargo,
            mutation_rate=0.3,
            n_jobs=n_jobs,
            seed=42,
        )

        end_time = time.time()
        duration = end_time - start_time

        logger.info(f"Evolution completed in {duration:.2f} seconds")
        logger.info(f"Best fitness: {best_fitness:.4f}")

        # Save results
        results = {
            "symbol": symbol,
            "timeframe": timeframe,
            "days": days,
            "parameters": {
                "pop_size": pop_size,
                "gens": gens,
                "n_folds": n_folds,
                "embargo": embargo,
                "n_jobs": n_jobs,
            },
            "best_fitness": best_fitness,
            "best_chromosome": best_chrom.to_dict(),
            "duration_seconds": duration,
            "data_points": len(df),
            "history": history,
            "timestamp": int(time.time()),
        }

        # Create output directory
        Path(outdir).mkdir(parents=True, exist_ok=True)

        # Save results
        timestamp = int(time.time())
        filename = f"ga_{symbol.replace('/', '_')}_{timestamp}.json"
        filepath = Path(outdir) / filename

        with open(filepath, "w") as f:
            json.dump(results, f, indent=2, default=str)

        logger.info(f"Results saved to {filepath}")

        # Save best chromosome as config
        config_filename = f"ga_best_{symbol.replace('/', '_')}.json"
        config_filepath = Path(outdir) / config_filename

        config = {
            "symbol": symbol,
            "timeframe": timeframe,
            "fitness": best_fitness,
            "chromosome": best_chrom.to_dict(),
            "timestamp": timestamp,
        }

        with open(config_filepath, "w") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Best chromosome saved to {config_filepath}")

        return results

    except Exception as e:
        logger.error(f"Error in run_ga: {e}")
        raise


def load_best_chromosome(
    symbol: str, outdir: str = "backend/data/ga"
) -> Chromosome | None:
    """
    Load best chromosome for a symbol.

    Args:
        symbol: Trading symbol
        outdir: Output directory

    Returns:
        Best chromosome or None if not found
    """
    try:
        config_filename = f"ga_best_{symbol.replace('/', '_')}.json"
        config_filepath = Path(outdir) / config_filename

        if not config_filepath.exists():
            logger.warning(f"No best chromosome found for {symbol}")
            return None

        with open(config_filepath) as f:
            config = json.load(f)

        chrom_dict = config.get("chromosome", {})
        if not chrom_dict:
            logger.error("No chromosome data in config file")
            return None

        return Chromosome.from_dict(chrom_dict)

    except Exception as e:
        logger.error(f"Error loading best chromosome for {symbol}: {e}")
        return None


def get_ga_status(outdir: str = "backend/data/ga") -> dict[str, Any]:
    """
    Get GA status and available results.

    Args:
        outdir: Output directory

    Returns:
        Status dictionary
    """
    try:
        out_path = Path(outdir)
        if not out_path.exists():
            return {"status": "no_results", "available_symbols": []}

        # Find all result files
        result_files = list(out_path.glob("ga_*_*.json"))
        best_files = list(out_path.glob("ga_best_*.json"))

        available_symbols = []
        for file in best_files:
            try:
                with open(file) as f:
                    config = json.load(f)
                symbol = config.get("symbol")
                if symbol:
                    available_symbols.append(symbol)
            except:
                continue

        return {
            "status": "ready",
            "available_symbols": available_symbols,
            "result_files": len(result_files),
            "best_files": len(best_files),
        }

    except Exception as e:
        logger.error(f"Error getting GA status: {e}")
        return {"status": "error", "error": str(e)}


def run_ga_batch(symbols: list, **kwargs) -> dict[str, Any]:
    """
    Run GA for multiple symbols.

    Args:
        symbols: List of trading symbols
        **kwargs: Additional parameters for run_ga

    Returns:
        Dictionary with results for each symbol
    """
    results = {}

    for symbol in symbols:
        try:
            logger.info(f"Running GA for {symbol}")
            result = run_ga(symbol=symbol, **kwargs)
            results[symbol] = result
        except Exception as e:
            logger.error(f"Error running GA for {symbol}: {e}")
            results[symbol] = {"error": str(e)}

    return results


def validate_chromosome_performance(
    symbol: str, chrom: Chromosome, days: int = 30
) -> dict[str, Any]:
    """
    Validate chromosome performance on recent data.

    Args:
        symbol: Trading symbol
        chrom: Chromosome to validate
        days: Number of days for validation

    Returns:
        Validation results
    """
    try:
        # Load recent data
        dfs = load_panel([symbol], "1m", days)
        df = dfs.get(symbol)

        if df is None or df.empty:
            return {"error": "No data available"}

        # Run validation
        from .wf import purged_walk_forward

        fitness = purged_walk_forward(df, chrom, n_folds=3, embargo=60)

        return {
            "symbol": symbol,
            "fitness": fitness,
            "data_points": len(df),
            "validation_days": days,
        }

    except Exception as e:
        logger.error(f"Error validating chromosome for {symbol}: {e}")
        return {"error": str(e)}
