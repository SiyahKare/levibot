from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RuntimeState:
    running: bool = False
    started_at: datetime | None = None
    equity: float | None = None
    daily_dd_pct: float | None = None
    open_positions: int = 0
    user_leverage: dict[str, int] = field(default_factory=dict)

    def start(self) -> None:
        if not self.running:
            self.running = True
            self.started_at = datetime.utcnow()

    def stop(self) -> None:
        self.running = False


STATE = RuntimeState()
