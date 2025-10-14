#!/usr/bin/env python3
"""Mock soak test for MarketFeeder → Engine integration."""

import asyncio
import os
import random
import statistics
import time
from datetime import datetime

SYMBOLS = os.getenv("SYMBOLS", "BTC/USDT,ETH/USDT,SOL/USDT").split(",")
DURATION_SEC = int(os.getenv("DURATION_SEC", "300"))  # 5 min
RATE_HZ = float(os.getenv("RATE_HZ", "30"))  # 30 md/sec per symbol
JITTER_MS = int(os.getenv("JITTER_MS", "5"))  # production jitter


class MockFeeder:
    """High-frequency mock market data feeder."""

    def __init__(self, symbols, rate_hz=30.0, jitter_ms=5):
        self.symbols = symbols
        self.dt = 1.0 / rate_hz
        self.jitter_ms = jitter_ms
        self.sent = 0
        self.dropped = 0

    async def push_loop(self, eng):
        """Push market data to engine at specified rate."""
        sym = eng.symbol
        next_t = time.perf_counter()

        while True:
            # Wait until next tick
            await asyncio.sleep(max(0, next_t - time.perf_counter()))

            ts = time.time()
            md = {
                "symbol": sym,
                "price": 100 + random.random() * 10,
                "spread": random.uniform(0.01, 0.2),
                "vol": random.uniform(1, 1000),
                "texts": [],
                "funding": 0.0,
                "oi": 0.0,
                "_ts": ts,
            }

            # Track drops based on queue fullness
            if eng._md_queue.full():
                self.dropped += 1

            await eng.push_md(md)
            self.sent += 1

            # Add jitter
            next_t += self.dt
            next_t += random.uniform(
                -self.jitter_ms / 1000, self.jitter_ms / 1000
            )

    async def run(self, manager, duration=DURATION_SEC):
        """Run mock feeding for specified duration."""
        tasks = []
        for s in SYMBOLS:
            eng = manager.engines.get(s)
            if eng:
                tasks.append(asyncio.create_task(self.push_loop(eng)))

        t0 = time.time()
        while time.time() - t0 < duration:
            await asyncio.sleep(1.0)

        # Cancel all tasks
        for t in tasks:
            t.cancel()
            try:
                await t
            except asyncio.CancelledError:
                pass


async def main():
    """Run mock soak test."""
    print(f"[MockSoak] start {datetime.utcnow().isoformat()}Z")
    print(f"Config: symbols={len(SYMBOLS)}, duration={DURATION_SEC}s, rate={RATE_HZ}Hz")
    print(f"Symbols: {', '.join(SYMBOLS)}\n")

    # Import here to ensure PYTHONPATH is set
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
    
    from src.engine.manager import EngineManager

    cfg = {
        "engine_defaults": {
            "cycle_interval": 0.02,  # 20ms cycle
            "md_queue_max": 128,
            "base_qty": 1.0,
        },
        "symbols_to_trade": SYMBOLS,
    }

    m = EngineManager(cfg)

    # Start engines only (no real feeder)
    for s in SYMBOLS:
        await m.start_engine(s)

    feeder = MockFeeder(SYMBOLS, rate_hz=RATE_HZ, jitter_ms=JITTER_MS)

    t0 = time.time()
    err_hist = []
    q_hist = []

    soak = asyncio.create_task(feeder.run(m, duration=DURATION_SEC))

    try:
        while not soak.done():
            # Health snapshot
            st = m.get_all_statuses()
            errs = sum(v.get("error_count", 0) for v in st.values())
            mean_q = (
                statistics.mean([eng._md_queue.qsize() for eng in m.engines.values()])
                if m.engines
                else 0
            )

            err_hist.append(errs)
            q_hist.append(mean_q)

            elapsed = int(time.time() - t0)
            print(
                f"[{elapsed:3d}s] running={len(st)} errors={errs} "
                f"q_mean={mean_q:.1f} sent={feeder.sent} dropped={feeder.dropped}"
            )

            await asyncio.sleep(1.0)

    finally:
        # Graceful shutdown
        await m.stop_all()

    # Summary and PASS/FAIL
    duration = time.time() - t0
    sent = feeder.sent
    dropped = feeder.dropped
    drop_rate = (dropped / max(1, sent)) * 100.0

    q95 = (
        statistics.quantiles(q_hist, n=20)[-1]
        if len(q_hist) >= 20
        else max(q_hist)
        if q_hist
        else 0.0
    )
    errors_total = max(err_hist) if err_hist else 0

    print("\n" + "=" * 50)
    print("MOCK SOAK SUMMARY")
    print("=" * 50)
    print(f"Symbols:        {len(SYMBOLS)}")
    print(f"Duration:       {duration:.1f}s")
    print(f"Rate:           {RATE_HZ} Hz/symbol")
    print(f"Messages sent:  {sent:,}")
    print(f"Messages drop:  {dropped:,}")
    print(f"Drop rate:      {drop_rate:.3f}%")
    print(f"Q95 depth:      {q95:.1f}")
    print(f"Errors total:   {errors_total}")
    print("=" * 50)

    # Acceptance criteria
    pass_drop = drop_rate <= 0.1
    pass_q = q95 <= 32
    pass_err = errors_total == 0

    print("\nAcceptance Criteria:")
    print(f"  Drop rate ≤ 0.1%:  {'✅ PASS' if pass_drop else '❌ FAIL'} ({drop_rate:.3f}%)")
    print(f"  Q95 depth ≤ 32:    {'✅ PASS' if pass_q else '❌ FAIL'} ({q95:.1f})")
    print(f"  Errors = 0:        {'✅ PASS' if pass_err else '❌ FAIL'} ({errors_total})")

    passed = pass_drop and pass_q and pass_err
    result = "PASS" if passed else "FAIL"
    
    print(f"\n{'🎉' if passed else '❌'} RESULT={result}")
    print("=" * 50 + "\n")

    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

