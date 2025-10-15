"""Replay service for backtesting and replay scenarios."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class ReplayStatus:
    """Replay status data class."""

    running: bool = False
    symbol: str | None = None
    window: str | None = None
    progress_pct: float = 0.0
    started_at: datetime | None = None
    current_ts: datetime | None = None
    bars_total: int = 0
    bars_done: int = 0


class ReplayService:
    """
    Replay service for feeding historical bars to engine.

    Supports:
    - Bar-by-bar replay at configurable speed
    - Progress tracking
    - Symbol-specific replay
    """

    def __init__(self):
        self.status = ReplayStatus()

    async def start(self, symbol: str, bars: list[dict], window: str = "backfill"):
        """
        Start replay for symbol.

        Args:
            symbol: Trading symbol
            bars: List of bar dictionaries with 'ts' field
            window: Window type (backfill, 24h, etc.)
        """
        self.status = ReplayStatus(
            running=True,
            symbol=symbol,
            window=window,
            progress_pct=0.0,
            started_at=datetime.now(UTC),
            current_ts=None,
            bars_total=len(bars),
            bars_done=0,
        )

        for i, bar in enumerate(bars):
            # Push bar to engine (real implementation would call engine_manager)
            # await engine_manager.push_md(symbol, bar)

            # Update progress
            await asyncio.sleep(0)  # yield to event loop
            self.status.bars_done = i + 1
            self.status.progress_pct = (
                100.0 * self.status.bars_done / max(1, self.status.bars_total)
            )
            self.status.current_ts = datetime.fromtimestamp(
                bar["ts"] / 1000, tz=UTC
            )

        self.status.running = False

    def get_status(self) -> ReplayStatus:
        """Get current replay status."""
        return self.status


# Global singleton
_replay_service = ReplayService()


def get_replay() -> ReplayService:
    """Get replay service singleton."""
    return _replay_service

