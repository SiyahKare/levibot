from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date


@dataclass
class DailyDrawdownTracker:
    start_equity: float
    day: date

    def compute_dd(self, current_equity: float) -> float:
        if self.start_equity <= 0:
            return 0.0
        return max(0.0, (self.start_equity - current_equity) / self.start_equity)

    def maybe_reset(self, now: datetime, current_equity: float) -> None:
        if now.date() != self.day:
            self.day = now.date()
            self.start_equity = current_equity


