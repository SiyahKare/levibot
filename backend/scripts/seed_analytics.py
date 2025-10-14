#!/usr/bin/env python3
"""
Analytics Dashboard Seed Script
Generates synthetic event data for testing analytics visualizations.
"""
import json
import os
import random
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Event configurations
EVENT_TYPES = [
    "SIGNAL_SCORED",
    "AUTO_ROUTE_EXECUTED", 
    "POSITION_OPENED",
    "POSITION_CLOSED",
    "TELEGRAM_REP_REFRESH",
    "DEX_QUOTE",
    "MEV_ARB_OPP",
    "L2_YIELDS",
    "NFT_FLOOR",
    "ALERT_TRIGGERED",
    "RISK_CHECK",
    "PAPER_ORDER",
    "ML_PREDICTION",
    "BACKTEST_RESULT",
]

SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT",
    "DOGEUSDT", "XRPUSDT", "DOTUSDT", "MATICUSDT", "AVAXUSDT",
    "LINKUSDT", "UNIUSDT", "ATOMUSDT", "LTCUSDT", "NEARUSDT",
]

# Weighted distribution for more realistic data
EVENT_WEIGHTS = {
    "SIGNAL_SCORED": 15,
    "AUTO_ROUTE_EXECUTED": 5,
    "POSITION_OPENED": 8,
    "POSITION_CLOSED": 8,
    "TELEGRAM_REP_REFRESH": 3,
    "DEX_QUOTE": 25,
    "MEV_ARB_OPP": 12,
    "L2_YIELDS": 5,
    "NFT_FLOOR": 2,
    "ALERT_TRIGGERED": 7,
    "RISK_CHECK": 10,
    "PAPER_ORDER": 6,
    "ML_PREDICTION": 8,
    "BACKTEST_RESULT": 4,
}

def generate_event(timestamp: datetime, trace_id: str = None) -> dict:
    """Generate a single synthetic event."""
    event_type = random.choices(EVENT_TYPES, weights=[EVENT_WEIGHTS[et] for et in EVENT_TYPES])[0]
    
    payload = {}
    
    # Add symbol for trading-related events
    if event_type in ["SIGNAL_SCORED", "AUTO_ROUTE_EXECUTED", "POSITION_OPENED", 
                      "POSITION_CLOSED", "PAPER_ORDER", "DEX_QUOTE"]:
        payload["symbol"] = random.choice(SYMBOLS)
    
    # Add event-specific payload data
    if event_type == "SIGNAL_SCORED":
        payload.update({
            "score": round(random.uniform(0.3, 0.95), 3),
            "confidence": round(random.uniform(0.5, 0.99), 3),
            "source": random.choice(["telegram", "twitter", "reddit", "discord"]),
        })
    elif event_type == "POSITION_OPENED":
        payload.update({
            "side": random.choice(["long", "short"]),
            "size_usd": round(random.uniform(100, 5000), 2),
            "entry_price": round(random.uniform(1000, 70000), 2),
        })
    elif event_type == "POSITION_CLOSED":
        payload.update({
            "pnl_usd": round(random.uniform(-500, 1500), 2),
            "pnl_pct": round(random.uniform(-15, 25), 2),
            "duration_sec": random.randint(300, 86400),
        })
    elif event_type == "MEV_ARB_OPP":
        payload.update({
            "dex_a": random.choice(["uniswap", "sushiswap", "pancakeswap"]),
            "dex_b": random.choice(["uniswap", "sushiswap", "pancakeswap"]),
            "profit_usd": round(random.uniform(5, 500), 2),
        })
    elif event_type == "DEX_QUOTE":
        payload.update({
            "price": round(random.uniform(1000, 70000), 2),
            "dex": random.choice(["uniswap", "sushiswap", "curve", "balancer"]),
        })
    elif event_type == "ALERT_TRIGGERED":
        payload.update({
            "severity": random.choice(["info", "low", "medium", "high", "critical"]),
            "title": random.choice([
                "High volatility detected",
                "Large position opened",
                "Stop loss triggered",
                "Risk limit exceeded",
                "New signal available",
            ]),
        })
    elif event_type == "L2_YIELDS":
        payload.update({
            "protocol": random.choice(["aave", "compound", "curve", "yearn"]),
            "apy": round(random.uniform(2, 25), 2),
        })
    elif event_type == "ML_PREDICTION":
        payload.update({
            "predicted_direction": random.choice(["up", "down", "neutral"]),
            "confidence": round(random.uniform(0.6, 0.95), 3),
        })
    
    event = {
        "ts": timestamp.isoformat(),
        "event_type": event_type,
        "payload": payload,
    }
    
    if trace_id:
        event["trace_id"] = trace_id
    
    return event

def generate_trace_events(base_time: datetime, num_events: int) -> list:
    """Generate a sequence of related events with the same trace_id."""
    trace_id = str(uuid.uuid4())[:16]
    events = []
    
    current_time = base_time
    for i in range(num_events):
        events.append(generate_event(current_time, trace_id))
        # Events in a trace are typically close together
        current_time += timedelta(seconds=random.randint(1, 120))
    
    return events

def seed_events(days: int = 7, events_per_day: int = 5000):
    """Generate and save synthetic events."""
    log_dir = Path(os.getenv("EVENT_LOG_DIR", "backend/data/logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    
    now = datetime.now(UTC)
    total_events = 0
    
    print("🌱 Seeding analytics data...")
    print(f"   Days: {days}")
    print(f"   Events per day: {events_per_day}")
    print(f"   Log directory: {log_dir}")
    print()
    
    for day_offset in range(days):
        day = now - timedelta(days=day_offset)
        day_str = day.strftime("%Y-%m-%d")
        
        # Create day directory
        day_dir = log_dir / day_str
        day_dir.mkdir(exist_ok=True)
        
        # Generate events file
        events_file = day_dir / "events_seed.jsonl"
        
        events_written = 0
        with open(events_file, "w") as f:
            remaining_events = events_per_day
            
            while remaining_events > 0:
                # Decide whether to create a trace or single event
                if random.random() < 0.3:  # 30% chance of trace
                    trace_size = random.randint(3, 10)
                    trace_size = min(trace_size, remaining_events)
                    
                    # Random time during the day
                    event_time = day.replace(
                        hour=random.randint(0, 23),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59),
                    )
                    
                    trace_events = generate_trace_events(event_time, trace_size)
                    for event in trace_events:
                        f.write(json.dumps(event) + "\n")
                        events_written += 1
                    
                    remaining_events -= trace_size
                else:
                    # Single event
                    event_time = day.replace(
                        hour=random.randint(0, 23),
                        minute=random.randint(0, 59),
                        second=random.randint(0, 59),
                    )
                    
                    event = generate_event(event_time)
                    f.write(json.dumps(event) + "\n")
                    events_written += 1
                    remaining_events -= 1
        
        total_events += events_written
        print(f"✅ {day_str}: {events_written:,} events written to {events_file.name}")
    
    print()
    print("🎉 Seeding complete!")
    print(f"   Total events generated: {total_events:,}")
    print(f"   Average per day: {total_events // days:,}")
    print()
    print("📊 Analytics dashboard should now show rich data!")
    print("   Visit: http://localhost:3001 → Analytics")

if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    events_per_day = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
    
    seed_events(days, events_per_day)

