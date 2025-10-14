#!/usr/bin/env python3
"""
Soak test for LeviBot engines.

Tests stability and performance over extended period.

Usage:
    python scripts/soak_test.py
    
    # Custom configuration
    API=http://localhost:8000 SYMBOLS="BTCUSDT,ETHUSDT" DURATION_MIN=60 python scripts/soak_test.py
"""

import asyncio
import json
import os
import statistics
import time

import aiohttp

# Configuration
API = os.getenv("API", "http://localhost:8000")
SYMBOLS = os.getenv("SYMBOLS", "BTCUSDT,ETHUSDT,SOLUSDT,ATOMUSDT,AVAXUSDT").split(",")
DURATION = int(os.getenv("DURATION_MIN", "30")) * 60  # Convert minutes to seconds
POLL = float(os.getenv("POLL_SEC", "5"))


async def start_symbol(session: aiohttp.ClientSession, symbol: str) -> dict:
    """Start engine for a symbol."""
    async with session.post(f"{API}/engines/start/{symbol}") as response:
        return await response.json()


async def get_status(session: aiohttp.ClientSession) -> dict:
    """Get engines status."""
    async with session.get(f"{API}/engines/status") as response:
        return await response.json()


async def get_risk(session: aiohttp.ClientSession) -> dict:
    """Get risk summary."""
    try:
        async with session.get(f"{API}/risk/summary") as response:
            return await response.json()
    except Exception:
        return {}


async def main():
    """Run soak test."""
    print("=" * 60)
    print("🧪 LeviBot Soak Test")
    print("=" * 60)
    print(f"API: {API}")
    print(f"Symbols: {', '.join(SYMBOLS)}")
    print(f"Duration: {DURATION/60:.0f} minutes")
    print(f"Poll interval: {POLL}s")
    print("=" * 60)
    
    async with aiohttp.ClientSession() as session:
        # Start all engines (idempotent)
        print("\n🚀 Starting engines...")
        for symbol in SYMBOLS:
            try:
                result = await start_symbol(session, symbol)
                print(f"  ✅ {symbol}: {result.get('status', 'started')}")
            except Exception as e:
                print(f"  ❌ {symbol}: {e}")
        
        print(f"\n⏱️  Starting {DURATION/60:.0f} minute soak test...\n")
        
        # Tracking
        start_time = time.time()
        error_history = []
        uptime_history = []
        latency_history = []
        crash_count = 0
        
        # Main monitoring loop
        while time.time() - start_time < DURATION:
            elapsed = int(time.time() - start_time)
            
            try:
                # Get engine status
                status = await get_status(session)
                engines = status.get("engines", [])
                
                # Calculate metrics
                total = status.get("total", 0)
                running = status.get("running", 0)
                crashed = status.get("crashed", 0)
                stopped = status.get("stopped", 0)
                
                # Error tracking
                total_errors = sum(e.get("error_count", 0) for e in engines)
                error_history.append(total_errors)
                
                # Uptime tracking
                uptimes = [e.get("uptime_seconds", 0) for e in engines if e.get("uptime_seconds", 0) > 0]
                if uptimes:
                    mean_uptime = statistics.mean(uptimes)
                    uptime_history.append(mean_uptime)
                else:
                    mean_uptime = 0
                
                # Crash tracking
                if crashed > 0:
                    crash_count += crashed
                
                # Get risk metrics
                risk = await get_risk(session)
                equity = risk.get("equity_now", 0)
                pnl_pct = risk.get("realized_today_pct", 0)
                positions = risk.get("positions_open", 0)
                
                # Print status
                print(
                    f"[{elapsed:4d}s] "
                    f"running={running}/{total} "
                    f"crashed={crashed} "
                    f"uptime={mean_uptime:.1f}s "
                    f"errs={total_errors} "
                    f"equity=${equity:.2f} "
                    f"pnl={pnl_pct:+.2f}% "
                    f"pos={positions}"
                )
            
            except Exception as e:
                print(f"[{elapsed:4d}s] ⚠️  Error polling status: {e}")
            
            # Sleep until next poll
            await asyncio.sleep(POLL)
        
        # Final summary
        print("\n" + "=" * 60)
        print("📊 Soak Test Summary")
        print("=" * 60)
        
        final_status = await get_status(session)
        final_risk = await get_risk(session)
        
        summary = {
            "test_config": {
                "symbols": len(SYMBOLS),
                "duration_minutes": DURATION / 60,
                "poll_interval_seconds": POLL,
            },
            "final_state": {
                "total_engines": final_status.get("total", 0),
                "running": final_status.get("running", 0),
                "crashed": final_status.get("crashed", 0),
                "stopped": final_status.get("stopped", 0),
            },
            "statistics": {
                "max_errors": max(error_history, default=0),
                "mean_uptime_seconds": statistics.mean(uptime_history) if uptime_history else 0,
                "total_crashes": crash_count,
            },
            "risk_metrics": {
                "final_equity": final_risk.get("equity_now", 0),
                "realized_pnl_pct": final_risk.get("realized_today_pct", 0),
                "final_positions": final_risk.get("positions_open", 0),
            },
        }
        
        print(json.dumps(summary, indent=2))
        
        # Pass/fail determination
        print("\n" + "=" * 60)
        if summary["statistics"]["total_crashes"] == 0:
            print("✅ PASS: No crashes detected")
        else:
            print(f"❌ FAIL: {summary['statistics']['total_crashes']} crashes detected")
        
        if summary["final_state"]["running"] == summary["final_state"]["total_engines"]:
            print("✅ PASS: All engines still running")
        else:
            print("❌ FAIL: Some engines stopped or crashed")
        
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

