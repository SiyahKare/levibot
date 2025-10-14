#!/usr/bin/env python3
"""
Nightly Replay & Drift Detection
Her gece son 24 saatlik Timescale verisi ile replay yaparak tolerans kontrolü
"""
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("❌ psycopg2 kurulu değil: pip install psycopg2-binary")
    sys.exit(1)


# Database connection
DSN = os.getenv(
    "PG_DSN",
    "postgresql://postgres:postgres@localhost:5432/levibot"
)

# Replay parameters
LOOKBACK_HOURS = int(os.getenv("REPLAY_HOURS", "24"))
TOLERANCE_PCT = float(os.getenv("REPLAY_TOLERANCE", "5.0"))  # %5 tolerance
OUTPUT_DIR = Path(os.getenv("REPLAY_OUTPUT", "./backend/data/reports"))


def fetch_market_data(from_ts: datetime) -> list[dict[str, Any]]:
    """Fetch market ticks from TimescaleDB."""
    try:
        conn = psycopg2.connect(DSN)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
        SELECT 
            EXTRACT(EPOCH FROM ts) as timestamp,
            symbol,
            last as price,
            volume
        FROM market_ticks
        WHERE ts >= %s
        ORDER BY ts ASC
        LIMIT 100000;
        """
        
        cur.execute(query, (from_ts,))
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"❌ Database error: {e}")
        return []


def fetch_paper_trades(from_ts: datetime) -> list[dict[str, Any]]:
    """Fetch paper trades for comparison."""
    try:
        conn = psycopg2.connect(DSN)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        query = """
        SELECT 
            symbol,
            side,
            qty,
            entry_price,
            exit_price,
            pnl_usd,
            entry_time,
            exit_time
        FROM paper_trades
        WHERE exit_time >= %s
        ORDER BY exit_time ASC;
        """
        
        cur.execute(query, (from_ts,))
        rows = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"⚠️  Paper trades table not found or error: {e}")
        return []


def simple_replay(market_data: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Simple replay engine - bu production'da gerçek engine'in offline modülü olmalı.
    Şimdilik basit bir simülasyon yapıyoruz.
    """
    if not market_data:
        return {"events": 0, "simulated_pnl": 0.0, "signals": 0}
    
    # Basit momentum stratejisi simülasyonu
    signals = []
    positions = {}
    pnl = 0.0
    
    for i, tick in enumerate(market_data):
        symbol = tick["symbol"]
        price = tick["price"]
        
        # Her 100. tick'te signal üret (örnek)
        if i % 100 == 0 and symbol not in positions:
            # Long aç
            positions[symbol] = {"entry": price, "qty": 1.0}
            signals.append({"symbol": symbol, "action": "buy", "price": price})
        
        # Pozisyon varsa ve %2 kar elde ettiyse kapat
        if symbol in positions:
            entry = positions[symbol]["entry"]
            pnl_pct = ((price - entry) / entry) * 100
            
            if pnl_pct > 2.0:
                trade_pnl = (price - entry) * positions[symbol]["qty"]
                pnl += trade_pnl
                signals.append({"symbol": symbol, "action": "sell", "price": price, "pnl": trade_pnl})
                del positions[symbol]
    
    return {
        "events": len(market_data),
        "simulated_pnl": round(pnl, 2),
        "signals": len(signals),
        "open_positions": len(positions),
    }


def drift_detection(
    actual_trades: list[dict[str, Any]],
    simulated_pnl: float
) -> dict[str, Any]:
    """
    Gerçek trades ile simülasyon sonucunu karşılaştır.
    Büyük fark varsa drift var demektir.
    """
    if not actual_trades:
        return {
            "drift_detected": False,
            "reason": "No actual trades to compare",
            "tolerance_ok": True,
        }
    
    actual_pnl = sum(t["pnl_usd"] for t in actual_trades)
    diff_pct = abs(actual_pnl - simulated_pnl) / max(abs(actual_pnl), 1.0) * 100
    
    drift_detected = diff_pct > TOLERANCE_PCT
    
    return {
        "drift_detected": drift_detected,
        "actual_pnl": round(actual_pnl, 2),
        "simulated_pnl": round(simulated_pnl, 2),
        "diff_pct": round(diff_pct, 2),
        "tolerance_pct": TOLERANCE_PCT,
        "tolerance_ok": not drift_detected,
    }


def generate_report() -> dict[str, Any]:
    """Main replay & drift check function."""
    from_ts = datetime.utcnow() - timedelta(hours=LOOKBACK_HOURS)
    
    print(f"🔍 Replay başlıyor: Son {LOOKBACK_HOURS} saat")
    print(f"📅 From: {from_ts.isoformat()}")
    
    # Fetch data
    market_data = fetch_market_data(from_ts)
    actual_trades = fetch_paper_trades(from_ts)
    
    if not market_data:
        return {
            "ok": False,
            "error": "No market data found",
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    # Replay
    replay_result = simple_replay(market_data)
    
    # Drift detection
    drift_result = drift_detection(actual_trades, replay_result["simulated_pnl"])
    
    # Final report
    report = {
        "ok": True,
        "timestamp": datetime.utcnow().isoformat(),
        "lookback_hours": LOOKBACK_HOURS,
        "from_timestamp": from_ts.isoformat(),
        "market_data": {
            "events": len(market_data),
            "symbols": len(set(d["symbol"] for d in market_data)),
        },
        "actual_trades": {
            "count": len(actual_trades),
            "total_pnl": sum(t["pnl_usd"] for t in actual_trades) if actual_trades else 0.0,
        },
        "replay": replay_result,
        "drift_detection": drift_result,
        "summary": {
            "tolerance_ok": drift_result["tolerance_ok"],
            "drift_detected": drift_result["drift_detected"],
            "recommendation": "✅ System OK" if drift_result["tolerance_ok"] else "⚠️  Investigate drift",
        },
    }
    
    return report


def save_report(report: dict[str, Any]) -> Path:
    """Save report to JSON file."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    filename = f"replay_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    filepath = OUTPUT_DIR / filename
    
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"💾 Rapor kaydedildi: {filepath}")
    return filepath


def main():
    """Main entry point."""
    print("=" * 60)
    print("🌙 LEVIBOT Nightly Replay & Drift Detection")
    print("=" * 60)
    
    try:
        report = generate_report()
        
        # Print summary
        print("\n📊 SONUÇ:")
        print(json.dumps(report, indent=2))
        
        # Save report
        save_report(report)
        
        # Exit code based on tolerance
        if not report.get("drift_detection", {}).get("tolerance_ok", True):
            print("\n⚠️  WARNING: Drift detected! Tolerans aşıldı.")
            sys.exit(1)
        
        print("\n✅ Replay tamamlandı - her şey normal")
        sys.exit(0)
        
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()

