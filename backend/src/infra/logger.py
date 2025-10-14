"""
Symbol-specific logging infrastructure.
"""

import logging
from datetime import datetime
from pathlib import Path


def get_engine_logger(symbol: str) -> logging.Logger:
    """
    Get a logger for a specific symbol.
    
    Logs to: data/logs/engine-{symbol}-{date}.jsonl
    
    Args:
        symbol: Trading symbol (e.g. "BTCUSDT")
    
    Returns:
        Logger instance
    """
    # Sanitize symbol (replace / with -)
    safe_symbol = symbol.replace("/", "-")
    
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"engine-{safe_symbol}-{date_str}.jsonl"
    
    logger = logging.getLogger(f"engine.{symbol}")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        # File handler (JSONL format)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter(
                '{"ts":"%(asctime)s","level":"%(levelname)s","symbol":"%(name)s","msg":"%(message)s"}'
            )
        )
        logger.addHandler(file_handler)
        
        # Console handler (human-readable)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt='%H:%M:%S'
            )
        )
        logger.addHandler(console_handler)
    
    return logger


def get_orchestrator_logger() -> logging.Logger:
    """
    Get logger for the orchestrator/manager.
    
    Logs to: data/logs/orchestrator-{date}.jsonl
    """
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"orchestrator-{date_str}.jsonl"
    
    logger = logging.getLogger("orchestrator")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter(
                '{"ts":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}'
            )
        )
        logger.addHandler(file_handler)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s [%(levelname)s] orchestrator: %(message)s',
                datefmt='%H:%M:%S'
            )
        )
        logger.addHandler(console_handler)
    
    return logger
