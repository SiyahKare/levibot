"""Gap filling utilities for OHLCV time-series data."""

from datetime import datetime, timezone


def minute_floor(ts_ms: int) -> int:
    """Floor timestamp to minute boundary."""
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    floored = dt.replace(second=0, microsecond=0)
    return int(floored.timestamp() * 1000)


def fill_minute_bars(ohlcv: list[list]) -> list[list]:
    """
    Fill missing minute bars with forward-fill from last close.

    Args:
        ohlcv: [[ms, o, h, l, c, v], ...] sorted ascending by timestamp

    Returns:
        Filled OHLCV with synthetic bars for gaps > 1 minute
    """
    if not ohlcv:
        return ohlcv

    filled = []
    i = 0
    cur = ohlcv[0]

    while i < len(ohlcv) - 1:
        nxt = ohlcv[i + 1]
        filled.append(cur)

        # Check for gaps > 1 minute
        dt = nxt[0] - cur[0]
        if dt > 60_000:
            steps = dt // 60_000 - 1
            for s in range(int(steps)):
                ts = cur[0] + 60_000 * (s + 1)
                o = h = l = c = cur[4]  # Forward-fill from last close
                v = 0.0  # Zero volume for synthetic bars
                filled.append([ts, o, h, l, c, v])

        cur = nxt
        i += 1

    filled.append(ohlcv[-1])
    return filled

