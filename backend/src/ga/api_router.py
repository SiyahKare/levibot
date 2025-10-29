"""GA API router for FastAPI integration."""

import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from .genes import Chromosome
from .runner import (
    get_ga_status,
    load_best_chromosome,
    run_ga,
    run_ga_batch,
    validate_chromosome_performance,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ga", tags=["Genetic Algorithm"])

# Global state for running jobs
_running_jobs: dict[str, dict[str, Any]] = {}
_executor = ThreadPoolExecutor(max_workers=2)


def require_admin_role():
    """Dependency for admin role requirement."""
    # TODO: Implement proper RBAC
    return {"role": "admin"}


@router.post("/run")
async def ga_run(
    symbol: str = Query("BTC/USDT", description="Trading symbol"),
    timeframe: str = Query("1m", description="Data timeframe"),
    days: int = Query(180, ge=30, le=365, description="Number of days to load"),
    pop_size: int = Query(36, ge=10, le=100, description="Population size"),
    gens: int = Query(15, ge=5, le=50, description="Number of generations"),
    n_folds: int = Query(6, ge=3, le=10, description="Number of folds"),
    embargo: int = Query(120, ge=60, le=500, description="Embargo period"),
    n_jobs: int = Query(1, ge=1, le=4, description="Number of parallel jobs"),
    background_tasks: BackgroundTasks = None,
    user: dict = Depends(require_admin_role),
):
    """
    Start GA optimization in background.

    Only admin users can trigger GA runs.
    """
    job_id = f"{symbol}_{int(time.time())}"

    if job_id in _running_jobs:
        raise HTTPException(status_code=400, detail="Job already running")

    # Start background task
    def run_ga_task():
        try:
            logger.info(f"Starting GA job {job_id} for {symbol}")
            _running_jobs[job_id] = {
                "status": "running",
                "symbol": symbol,
                "start_time": time.time(),
                "progress": 0,
            }

            result = run_ga(
                symbol=symbol,
                timeframe=timeframe,
                days=days,
                pop_size=pop_size,
                gens=gens,
                n_folds=n_folds,
                embargo=embargo,
                n_jobs=n_jobs,
            )

            _running_jobs[job_id] = {
                "status": "completed",
                "symbol": symbol,
                "start_time": _running_jobs[job_id]["start_time"],
                "end_time": time.time(),
                "result": result,
            }

            logger.info(f"GA job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"GA job {job_id} failed: {e}")
            _running_jobs[job_id] = {
                "status": "failed",
                "symbol": symbol,
                "start_time": _running_jobs[job_id]["start_time"],
                "end_time": time.time(),
                "error": str(e),
            }

    # Submit to thread pool
    future = _executor.submit(run_ga_task)

    return {
        "ok": True,
        "message": "GA optimization started",
        "job_id": job_id,
        "symbol": symbol,
        "parameters": {
            "timeframe": timeframe,
            "days": days,
            "pop_size": pop_size,
            "gens": gens,
            "n_folds": n_folds,
            "embargo": embargo,
            "n_jobs": n_jobs,
        },
    }


@router.get("/status")
async def ga_status():
    """Get GA system status and running jobs."""
    try:
        system_status = get_ga_status()

        # Add running jobs info
        running_jobs = []
        for job_id, job_info in _running_jobs.items():
            if job_info["status"] == "running":
                duration = time.time() - job_info["start_time"]
                running_jobs.append(
                    {
                        "job_id": job_id,
                        "symbol": job_info["symbol"],
                        "duration_seconds": duration,
                        "status": "running",
                    }
                )

        return {
            "ok": True,
            "system_status": system_status,
            "running_jobs": running_jobs,
            "total_jobs": len(_running_jobs),
        }

    except Exception as e:
        logger.error(f"Error getting GA status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/best")
async def ga_best(symbol: str = Query("BTC/USDT", description="Trading symbol")):
    """Get best chromosome for a symbol."""
    try:
        best_chrom = load_best_chromosome(symbol)

        if best_chrom is None:
            return {"ok": False, "error": "No best chromosome found", "symbol": symbol}

        return {
            "ok": True,
            "symbol": symbol,
            "chromosome": best_chrom.to_dict(),
            "message": "Best chromosome loaded successfully",
        }

    except Exception as e:
        logger.error(f"Error loading best chromosome for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs")
async def ga_jobs():
    """Get all GA jobs (running and completed)."""
    try:
        jobs = []
        for job_id, job_info in _running_jobs.items():
            job_data = {
                "job_id": job_id,
                "symbol": job_info["symbol"],
                "status": job_info["status"],
                "start_time": job_info["start_time"],
            }

            if "end_time" in job_info:
                job_data["end_time"] = job_info["end_time"]
                job_data["duration_seconds"] = (
                    job_info["end_time"] - job_info["start_time"]
                )

            if "error" in job_info:
                job_data["error"] = job_info["error"]

            if "result" in job_info:
                job_data["best_fitness"] = job_info["result"].get("best_fitness")

            jobs.append(job_data)

        return {"ok": True, "jobs": jobs, "total_jobs": len(jobs)}

    except Exception as e:
        logger.error(f"Error getting GA jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}")
async def ga_job_detail(job_id: str):
    """Get detailed information about a specific job."""
    try:
        if job_id not in _running_jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job_info = _running_jobs[job_id]

        return {"ok": True, "job_id": job_id, "job_info": job_info}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job details for {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def ga_validate(
    symbol: str = Query("BTC/USDT", description="Trading symbol"),
    chromosome: dict = None,
    days: int = Query(30, ge=7, le=90, description="Validation days"),
):
    """Validate a chromosome on recent data."""
    try:
        if chromosome is None:
            # Load best chromosome
            best_chrom = load_best_chromosome(symbol)
            if best_chrom is None:
                raise HTTPException(status_code=404, detail="No best chromosome found")
        else:
            # Create chromosome from provided data
            best_chrom = Chromosome.from_dict(chromosome)

        # Validate performance
        result = validate_chromosome_performance(symbol, best_chrom, days)

        return {"ok": True, "validation_result": result}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating chromosome for {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch")
async def ga_batch_run(
    symbols: list[str] = Query(..., description="List of trading symbols"),
    timeframe: str = Query("1m", description="Data timeframe"),
    days: int = Query(180, ge=30, le=365, description="Number of days to load"),
    pop_size: int = Query(36, ge=10, le=100, description="Population size"),
    gens: int = Query(15, ge=5, le=50, description="Number of generations"),
    background_tasks: BackgroundTasks = None,
    user: dict = Depends(require_admin_role),
):
    """Run GA for multiple symbols in batch."""
    try:
        if len(symbols) > 5:
            raise HTTPException(
                status_code=400, detail="Maximum 5 symbols allowed in batch"
            )

        # Start batch job
        def run_batch_task():
            try:
                logger.info(f"Starting batch GA for {symbols}")
                results = run_ga_batch(
                    symbols=symbols,
                    timeframe=timeframe,
                    days=days,
                    pop_size=pop_size,
                    gens=gens,
                )

                # Store batch results
                batch_id = f"batch_{int(time.time())}"
                _running_jobs[batch_id] = {
                    "status": "completed",
                    "type": "batch",
                    "symbols": symbols,
                    "results": results,
                }

                logger.info(f"Batch GA completed for {symbols}")

            except Exception as e:
                logger.error(f"Batch GA failed: {e}")
                batch_id = f"batch_{int(time.time())}"
                _running_jobs[batch_id] = {
                    "status": "failed",
                    "type": "batch",
                    "symbols": symbols,
                    "error": str(e),
                }

        # Submit to thread pool
        future = _executor.submit(run_batch_task)

        return {
            "ok": True,
            "message": "Batch GA optimization started",
            "symbols": symbols,
            "parameters": {
                "timeframe": timeframe,
                "days": days,
                "pop_size": pop_size,
                "gens": gens,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting batch GA: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/jobs/{job_id}")
async def ga_cancel_job(job_id: str, user: dict = Depends(require_admin_role)):
    """Cancel a running GA job."""
    try:
        if job_id not in _running_jobs:
            raise HTTPException(status_code=404, detail="Job not found")

        job_info = _running_jobs[job_id]
        if job_info["status"] != "running":
            raise HTTPException(status_code=400, detail="Job is not running")

        # Mark as cancelled
        _running_jobs[job_id]["status"] = "cancelled"
        _running_jobs[job_id]["end_time"] = time.time()

        return {"ok": True, "message": f"Job {job_id} cancelled", "job_id": job_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Import time module
import time
