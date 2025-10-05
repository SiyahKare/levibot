from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional


@dataclass
class RuntimeState:
    running: bool = False
    started_at: Optional[datetime] = None
    equity: Optional[float] = None
    daily_dd_pct: Optional[float] = None
    open_positions: int = 0
    user_leverage: Dict[str, int] = field(default_factory=dict)

    def start(self) -> None:
        if not self.running:
            self.running = True
            self.started_at = datetime.utcnow()

    def stop(self) -> None:
        self.running = False


STATE = RuntimeState()


