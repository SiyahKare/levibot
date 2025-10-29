"""Genetic Algorithm core implementation."""

import logging
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import numpy as np
import pandas as pd

from .genes import Chromosome, random_chrom, validate_chromosome
from .wf import purged_walk_forward

logger = logging.getLogger(__name__)


def mutate(chrom: Chromosome, rate: float = 0.2) -> Chromosome:
    """
    Mutate chromosome with given rate.

    Args:
        chrom: Original chromosome
        rate: Mutation rate

    Returns:
        Mutated chromosome
    """
    c = Chromosome(**chrom.to_dict())

    # Model parameters
    if random.random() < rate:
        c.model_type = random.choice([0, 1])

    if random.random() < rate:
        c.rf_n_estimators = max(20, c.rf_n_estimators + random.randint(-20, 20))

    if random.random() < rate:
        c.rf_max_depth = max(2, c.rf_max_depth + random.randint(-2, 2))

    if random.random() < rate:
        c.lr_C = 10 ** random.uniform(-3, 1)

    # Technical indicators
    if random.random() < rate:
        c.rsi_len = max(5, min(30, c.rsi_len + random.randint(-2, 2)))

    if random.random() < rate:
        c.rsi_buy = max(10, min(45, c.rsi_buy + random.randint(-5, 5)))

    if random.random() < rate:
        c.rsi_sell = max(50, min(90, c.rsi_sell + random.randint(-5, 5)))
        if c.rsi_sell <= c.rsi_buy:
            c.rsi_sell = c.rsi_buy + 10

    if random.random() < rate:
        c.ema_fast = max(5, min(100, c.ema_fast + random.randint(-5, 5)))

    if random.random() < rate:
        c.ema_slow = max(50, min(300, c.ema_slow + random.randint(-10, 10)))
        if c.ema_slow <= c.ema_fast:
            c.ema_slow = c.ema_fast + 20

    # Risk management
    if random.random() < rate:
        c.tp_bps = max(5, min(200, c.tp_bps + random.randint(-10, 10)))

    if random.random() < rate:
        c.sl_bps = max(5, min(150, c.sl_bps + random.randint(-10, 10)))

    if random.random() < rate:
        c.hold_bars = max(10, min(500, c.hold_bars + random.randint(-20, 20)))

    if random.random() < rate:
        c.risk_bps = max(5, min(100, c.risk_bps + random.randint(-5, 5)))

    # Portfolio management
    if random.random() < rate:
        c.regime_filter = random.choice([0, 1])

    if random.random() < rate:
        c.vol_target_pct = random.choice([10, 15, 20, 25, 30])

    if random.random() < rate:
        c.max_leverage = random.choice([1, 2, 3])

    # Label generation
    if random.random() < rate:
        c.tb_u_bps = max(10, min(200, c.tb_u_bps + random.randint(-10, 10)))

    if random.random() < rate:
        c.tb_d_bps = max(10, min(200, c.tb_d_bps + random.randint(-10, 10)))

    if random.random() < rate:
        c.tb_t_bars = max(10, min(500, c.tb_t_bars + random.randint(-20, 20)))

    # Validate and fix if needed
    if not validate_chromosome(c):
        logger.warning("Generated invalid chromosome, using original")
        return chrom

    return c


def crossover(parent1: Chromosome, parent2: Chromosome) -> Chromosome:
    """
    Create offspring from two parents.

    Args:
        parent1: First parent
        parent2: Second parent

    Returns:
        Offspring chromosome
    """

    def pick(x, y):
        return random.choice([x, y])

    child = Chromosome(
        # Model parameters
        model_type=pick(parent1.model_type, parent2.model_type),
        rf_n_estimators=pick(parent1.rf_n_estimators, parent2.rf_n_estimators),
        rf_max_depth=pick(parent1.rf_max_depth, parent2.rf_max_depth),
        lr_C=pick(parent1.lr_C, parent2.lr_C),
        # Technical indicators
        rsi_len=pick(parent1.rsi_len, parent2.rsi_len),
        rsi_buy=pick(parent1.rsi_buy, parent2.rsi_buy),
        rsi_sell=pick(parent1.rsi_sell, parent2.rsi_sell),
        ema_fast=pick(parent1.ema_fast, parent2.ema_fast),
        ema_slow=pick(parent1.ema_slow, parent2.ema_slow),
        # Risk management
        tp_bps=pick(parent1.tp_bps, parent2.tp_bps),
        sl_bps=pick(parent1.sl_bps, parent2.sl_bps),
        hold_bars=pick(parent1.hold_bars, parent2.hold_bars),
        risk_bps=pick(parent1.risk_bps, parent2.risk_bps),
        # Portfolio management
        regime_filter=pick(parent1.regime_filter, parent2.regime_filter),
        vol_target_pct=pick(parent1.vol_target_pct, parent2.vol_target_pct),
        max_leverage=pick(parent1.max_leverage, parent2.max_leverage),
        # Label generation
        tb_u_bps=pick(parent1.tb_u_bps, parent2.tb_u_bps),
        tb_d_bps=pick(parent1.tb_d_bps, parent2.tb_d_bps),
        tb_t_bars=pick(parent1.tb_t_bars, parent2.tb_t_bars),
    )

    # Validate and fix if needed
    if not validate_chromosome(child):
        logger.warning("Generated invalid child, using parent1")
        return parent1

    return child


def evaluate_population(
    population: list[Chromosome],
    df: pd.DataFrame,
    n_folds: int = 5,
    embargo: int = 120,
    n_jobs: int = 1,
) -> list[float]:
    """
    Evaluate population fitness in parallel.

    Args:
        population: List of chromosomes
        df: OHLCV DataFrame
        n_folds: Number of folds for validation
        embargo: Embargo period
        n_jobs: Number of parallel jobs

    Returns:
        List of fitness scores
    """
    if n_jobs == 1:
        # Sequential evaluation
        scores = []
        for i, chrom in enumerate(population):
            try:
                score = purged_walk_forward(df, chrom, n_folds, embargo)
                scores.append(score)
                logger.debug(f"Chromosome {i}: fitness={score:.4f}")
            except Exception as e:
                logger.error(f"Error evaluating chromosome {i}: {e}")
                scores.append(-10.0)
        return scores

    # Parallel evaluation
    scores = [-10.0] * len(population)

    with ThreadPoolExecutor(max_workers=n_jobs) as executor:
        future_to_idx = {
            executor.submit(purged_walk_forward, df, chrom, n_folds, embargo): i
            for i, chrom in enumerate(population)
        }

        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                score = future.result()
                scores[idx] = score
                logger.debug(f"Chromosome {idx}: fitness={score:.4f}")
            except Exception as e:
                logger.error(f"Error evaluating chromosome {idx}: {e}")
                scores[idx] = -10.0

    return scores


def evolve(
    df: pd.DataFrame,
    pop_size: int = 30,
    gens: int = 12,
    elite_frac: float = 0.3,
    n_folds: int = 5,
    embargo: int = 120,
    mutation_rate: float = 0.3,
    n_jobs: int = 1,
    seed: int = 42,
) -> tuple[Chromosome, float, list[dict]]:
    """
    Run genetic algorithm evolution.

    Args:
        df: OHLCV DataFrame
        pop_size: Population size
        gens: Number of generations
        elite_frac: Fraction of elite to keep
        n_folds: Number of folds for validation
        embargo: Embargo period
        mutation_rate: Mutation rate
        n_jobs: Number of parallel jobs
        seed: Random seed

    Returns:
        Tuple of (best_chromosome, best_fitness, history)
    """
    random.seed(seed)
    np.random.seed(seed)

    logger.info(
        f"Starting GA evolution: pop_size={pop_size}, gens={gens}, "
        f"n_folds={n_folds}, embargo={embargo}"
    )

    # Initialize population
    population = [random_chrom() for _ in range(pop_size)]
    history = []
    best_overall = None
    best_fitness = -np.inf

    for generation in range(1, gens + 1):
        logger.info(f"Generation {generation}/{gens}")

        # Evaluate population
        scores = evaluate_population(population, df, n_folds, embargo, n_jobs)

        # Track best
        best_idx = np.argmax(scores)
        best_score = scores[best_idx]
        best_chrom = population[best_idx]

        if best_score > best_fitness:
            best_fitness = best_score
            best_overall = best_chrom

        # Record history
        history.append(
            {
                "generation": generation,
                "best_fitness": best_score,
                "avg_fitness": np.mean(scores),
                "std_fitness": np.std(scores),
                "best_chromosome": best_chrom.to_dict(),
            }
        )

        logger.info(
            f"Generation {generation}: best={best_score:.4f}, "
            f"avg={np.mean(scores):.4f}, std={np.std(scores):.4f}"
        )

        # Selection and reproduction
        elite_size = max(1, int(pop_size * elite_frac))

        # Rank by fitness
        ranked_indices = np.argsort(scores)[::-1]
        elite = [population[i] for i in ranked_indices[:elite_size]]

        # Create next generation
        next_generation = elite.copy()

        while len(next_generation) < pop_size:
            # Tournament selection
            parent1 = tournament_selection(population, scores, tournament_size=3)
            parent2 = tournament_selection(population, scores, tournament_size=3)

            # Crossover
            child = crossover(parent1, parent2)

            # Mutation
            child = mutate(child, mutation_rate)

            next_generation.append(child)

        population = next_generation

    logger.info(f"GA evolution completed. Best fitness: {best_fitness:.4f}")

    return best_overall, best_fitness, history


def tournament_selection(
    population: list[Chromosome], scores: list[float], tournament_size: int = 3
) -> Chromosome:
    """
    Tournament selection for parent selection.

    Args:
        population: List of chromosomes
        scores: List of fitness scores
        tournament_size: Tournament size

    Returns:
        Selected chromosome
    """
    tournament_indices = random.sample(range(len(population)), tournament_size)
    tournament_scores = [scores[i] for i in tournament_indices]
    winner_idx = tournament_indices[np.argmax(tournament_scores)]
    return population[winner_idx]


def get_population_stats(
    population: list[Chromosome], scores: list[float]
) -> dict[str, Any]:
    """Get population statistics."""
    return {
        "size": len(population),
        "best_fitness": max(scores),
        "worst_fitness": min(scores),
        "avg_fitness": np.mean(scores),
        "std_fitness": np.std(scores),
        "median_fitness": np.median(scores),
    }
