"""
Trading engine for a single symbol.
"""

import asyncio
import time
from enum import Enum
from typing import Any

from ..metrics.metrics import export_engine_health, export_signal, inference_latency
from ..ml.features.onchain_fetcher import MockOnchainProvider, OnchainFetcher
from ..ml.features.sentiment_extractor import (
    GemmaSentimentProvider,
    SentimentExtractor,
)
from ..ml.models.ensemble_predictor import EnsemblePredictor
from ..risk.manager import RiskManager


class EngineStatus(Enum):
    """Engine lifecycle states."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    CRASHED = "crashed"
    STOPPING = "stopping"


class TradingEngine:
    """
    Independent trading engine for a single symbol.

    Responsibilities:
    - Market data subscription (websocket)
    - Signal generation (ML model inference)
    - Order execution (paper or live)
    - PnL tracking
    - State persistence
    """

    def __init__(
        self,
        symbol: str,
        config: dict[str, Any],
        logger: Any,
    ):
        self.symbol = symbol
        self.config = config
        self.logger = logger

        # Lifecycle
        self.status = EngineStatus.STOPPED
        self.start_time: float | None = None
        self.last_heartbeat: float | None = None

        # Error tracking
        self.error_count = 0
        self.last_error: str | None = None

        # Trading state
        self.position: float | None = None
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        self.trade_count = 0

        # Internal
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._ws_connection = None

        # ML components (lazy init in _run)
        self._ensemble: EnsemblePredictor | None = None
        self._sentiment: SentimentExtractor | None = None
        self._onchain: OnchainFetcher | None = None

        # Risk manager
        base_equity = float(config.get("equity_base", 10000.0))
        self.risk = RiskManager(base_equity=base_equity)

    async def start(self) -> None:
        """Start the engine (non-blocking)."""
        if self.status != EngineStatus.STOPPED:
            raise RuntimeError(f"Engine {self.symbol} already running")

        self.status = EngineStatus.STARTING
        self.start_time = time.time()
        self.logger.info(f"Starting engine for {self.symbol}")

        # Spawn main task
        self._task = asyncio.create_task(self._run())

    async def stop(self, timeout: float = 10.0) -> None:
        """Stop the engine gracefully."""
        if self.status == EngineStatus.STOPPED:
            return

        self.status = EngineStatus.STOPPING
        self.logger.info(f"Stopping engine for {self.symbol}")
        self._stop_event.set()

        # Wait for task to finish
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=timeout)
            except TimeoutError:
                self.logger.warning(
                    f"Engine {self.symbol} stop timeout, cancelling task"
                )
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

        self.status = EngineStatus.STOPPED
        self.logger.info(f"Engine {self.symbol} stopped")

    async def _run(self) -> None:
        """Main engine loop."""
        try:
            self.status = EngineStatus.RUNNING

            # Initialize ML components
            self._init_ml_components()

            # Initialize components
            await self._connect_market_data()
            await self._load_state()

            # Main loop
            while not self._stop_event.is_set():
                self.last_heartbeat = time.time()

                try:
                    # Trading cycle
                    market_data = await self._get_market_data()
                    signal = await self._generate_signal(market_data)

                    if self._check_risk(signal) and signal:
                        await self._execute_order(signal)

                    await self._persist_state()

                    # Export health metrics
                    try:
                        export_engine_health(self.symbol, self.get_health())
                    except Exception as e:
                        self.logger.warning(f"Failed to export health metrics: {e}")

                    # Sleep interval (configurable)
                    cycle_interval = self.config.get("cycle_interval", 1.0)
                    await asyncio.sleep(cycle_interval)

                except Exception as e:
                    self.error_count += 1
                    self.last_error = str(e)
                    self.logger.error(
                        f"Error in trading cycle: {e}",
                        exc_info=True,
                        extra={"symbol": self.symbol, "error_count": self.error_count},
                    )

                    # Exponential backoff (max 60s)
                    backoff = min(2**self.error_count, 60)
                    await asyncio.sleep(backoff)

        except Exception as e:
            self.status = EngineStatus.CRASHED
            self.last_error = str(e)
            self.logger.error(
                f"Engine {self.symbol} crashed: {e}",
                exc_info=True,
                extra={"symbol": self.symbol},
            )

        finally:
            await self._cleanup()

    # ========== ML Components ==========

    def _init_ml_components(self) -> None:
        """Initialize ML components (ensemble, sentiment, on-chain)."""
        # Ensemble predictor
        ai_config = self.config.get("ai", {})
        ensemble_cfg = ai_config.get("ensemble", {})
        self._ensemble = EnsemblePredictor(
            w_lgbm=ensemble_cfg.get("w_lgbm", 0.5),
            w_tft=ensemble_cfg.get("w_tft", 0.3),
            w_sent=ensemble_cfg.get("w_sent", 0.2),
            threshold=ensemble_cfg.get("threshold", 0.55),
        )

        # Sentiment extractor
        sentiment_cfg = ai_config.get("sentiment", {})
        provider = GemmaSentimentProvider(rpm=sentiment_cfg.get("rpm", 60))
        self._sentiment = SentimentExtractor(
            provider=provider, ttl_seconds=sentiment_cfg.get("ttl", 900)
        )

        # On-chain fetcher
        onchain_cfg = ai_config.get("onchain", {})
        # TODO: Support real providers (Dune, Nansen)
        onchain_provider = MockOnchainProvider()
        self._onchain = OnchainFetcher(
            provider=onchain_provider, ttl_seconds=onchain_cfg.get("ttl", 300)
        )

        self.logger.info(f"ML components initialized for {self.symbol}")

    # ========== Market Data Hooks (to be implemented) ==========

    async def _connect_market_data(self) -> None:
        """Connect to market data source (websocket)."""
        self.logger.info(f"Connecting to market data for {self.symbol}")
        # TODO: Implement websocket connection

    async def _get_market_data(self) -> dict[str, Any]:
        """Get latest market data."""
        # TODO: Implement
        return {}

    # ========== Trading Logic Hooks (to be implemented) ==========

    async def _generate_signal(self, market_data: dict) -> dict | None:
        """
        Generate trading signal using ML ensemble.

        Combines:
        - Technical features (from market_data)
        - On-chain metrics (from Dune/Nansen)
        - Sentiment scores (from Gemma/news)
        """
        if not self._ensemble or not self._sentiment or not self._onchain:
            return None

        try:
            # 1. Get on-chain metrics
            onchain_metrics = await self._onchain.get_metrics(self.symbol)

            # 2. Build feature dictionary
            features = {
                "vol": market_data.get("vol", 0.0),
                "spread": market_data.get("spread", 0.0),
                "funding_rate": onchain_metrics.get("funding_rate", 0.0),
                "inflow": onchain_metrics.get("exchange_inflow", 0.0),
                "outflow": onchain_metrics.get("exchange_outflow", 0.0),
                "whale_txs": onchain_metrics.get("whale_txs", 0.0),
            }

            # 3. Get sentiment score
            # TODO: Get real news/tweet texts from market_data
            texts = market_data.get("texts", [])
            sentiment = await self._sentiment.score(f"{self.symbol}:latest", texts)

            # 4. Run ensemble predictor (with latency tracking)
            t_start = time.time()
            prediction = self._ensemble.predict(features, sentiment)
            inference_time = time.time() - t_start

            # Track inference latency
            try:
                inference_latency.labels(self.symbol).observe(inference_time)
            except Exception:
                pass  # Don't fail signal generation on metrics error

            # 5. Generate signal if not flat
            if prediction["side"] == "flat":
                return None

            # 6. Calculate position size based on confidence
            size = self._calculate_position_size(prediction["confidence"])

            return {
                "symbol": self.symbol,
                "side": prediction["side"],
                "size": size,
                "prob_up": prediction["prob_up"],
                "confidence": prediction["confidence"],
                "sentiment": sentiment,
                "features": features,
            }

        except Exception as e:
            self.logger.error(f"Error generating signal: {e}", exc_info=True)
            return None

    def _check_risk(self, signal: dict | None) -> bool:
        """
        Check if signal passes risk filters.

        Checks:
        - Global stop loss
        - Concurrent position limits
        """
        if not signal:
            return False

        # Global stop check
        if self.risk.is_global_stop():
            self.logger.warning(
                f"Global stop active (daily loss: {self.risk.realized_today_pct():.2f}%), skipping order"
            )
            return False

        # Concurrent positions check
        if not self.risk.can_open_new_position(self.symbol):
            self.logger.info(
                f"Max concurrent positions ({self.risk.policy.max_concurrent_positions}) reached, skipping order"
            )
            return False

        return True

    async def _execute_order(self, signal: dict) -> None:
        """
        Execute order based on signal.

        Calculates notional using risk manager and logs trade.
        TODO: Implement real order execution (Epic-4)
        """
        # Get volatility (mock for now - TODO: get from market data)
        vol_annual = float(self.config.get("vol_ann", 0.6))

        # Calculate position size using risk manager
        prob_up = signal["prob_up"]
        confidence = signal["confidence"]
        risk_fraction = self.risk.calc_position_size(
            self.symbol, prob_up, confidence, vol_annual
        )

        # Calculate notional
        equity = self.risk.book.equity_now
        notional = equity * risk_fraction

        # Update signal with sizing info
        signal["notional"] = round(notional, 2)
        signal["risk_fraction"] = round(risk_fraction, 4)
        signal["equity"] = round(equity, 2)

        # Log execution
        self.logger.info(
            f"EXEC {self.symbol} {signal['side']} "
            f"notional=${notional:.2f} ({risk_fraction*100:.1f}% of equity) "
            f"confidence={confidence:.2f} prob_up={prob_up:.2f}",
            extra={"symbol": self.symbol, "signal": signal},
        )

        # Update trade count
        self.trade_count += 1

        # Track in risk manager
        self.risk.on_order_filled(
            self.symbol,
            signal["side"],
            notional,
            realized_pnl=0.0,  # TODO: track actual PnL
        )

        # Export signal metrics
        try:
            export_signal(self.symbol, prob_up, confidence, signal["side"])
        except Exception as e:
            self.logger.warning(f"Failed to export signal metrics: {e}")

    def _calculate_position_size(self, confidence: float) -> float:
        """
        Calculate position size for signal generation.

        Note: This is now just a placeholder for backward compatibility.
        Real sizing is done in _execute_order() via RiskManager.

        Returns confidence-based size for signal metadata.
        """
        return confidence

    # ========== State Management ==========

    async def _load_state(self) -> None:
        """Load persisted state from disk/redis."""
        # TODO: Implement state loading
        pass

    async def _persist_state(self) -> None:
        """Update and persist state."""
        # TODO: Implement state persistence
        pass

    async def _cleanup(self) -> None:
        """Cleanup resources."""
        if self._ws_connection:
            try:
                await self._ws_connection.close()
            except Exception as e:
                self.logger.warning(f"Error closing websocket: {e}")

    # ========== Health & Metrics ==========

    def get_health(self) -> dict[str, Any]:
        """Get engine health metrics."""
        uptime = time.time() - self.start_time if self.start_time else 0

        return {
            "symbol": self.symbol,
            "status": self.status.value,
            "uptime_seconds": round(uptime, 2),
            "last_heartbeat": self.last_heartbeat,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "position": self.position,
            "daily_pnl": round(self.daily_pnl, 2),
            "total_pnl": round(self.total_pnl, 2),
            "trade_count": self.trade_count,
        }
