#!/usr/bin/env python3
"""
LEVIBOT Realtime Health Validator

Checks all critical components:
- API health & metrics
- Panel availability
- SSE stream connectivity
- Redis streams
- TimescaleDB hypertables
- Paper trading engine
"""
import json
import os
import socket
import sys
import time
from contextlib import closing
from typing import Any

try:
    import requests
except ImportError:
    print("ERROR: requests not installed. Run: pip install requests")
    sys.exit(1)

API = os.getenv("API_URL", "http://localhost:8000")
PANEL = os.getenv("PANEL_URL", "http://localhost:3001")


def port_open(host: str, port: int) -> bool:
    """Check if a TCP port is open."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.settimeout(0.8)
        return s.connect_ex((host, port)) == 0


def get(url: str, timeout: int = 3) -> requests.Response:
    """HTTP GET with timeout."""
    return requests.get(url, timeout=timeout)


def sse_read(url: str, seconds: int = 5) -> int:
    """Read SSE stream and count events."""
    try:
        import sseclient
    except ImportError:
        print("INFO: sseclient-py not installed, skipping SSE test")
        return -1
    
    try:
        r = requests.get(url, stream=True, timeout=seconds + 2)
        client = sseclient.SSEClient(r)
        start = time.time()
        cnt = 0
        for e in client.events():
            cnt += 1
            if time.time() - start > seconds:
                break
        return cnt
    except Exception as e:
        print(f"SSE error: {e}")
        return 0


def redis_check() -> tuple[bool, dict[str, Any]]:
    """Check Redis connectivity and streams."""
    try:
        import redis
    except ImportError:
        return False, {"error": "redis package not installed"}
    
    try:
        r = redis.Redis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
            socket_connect_timeout=2
        )
        info = r.info()
        
        # Check for streams (both old and new format)
        streams = []
        for pattern in ["stream:*", "ticks", "signals", "events"]:
            keys = r.keys(pattern)
            if keys:
                streams.extend(keys)
        
        return True, {
            "used_memory_human": info.get("used_memory_human"),
            "uptime_seconds": info.get("uptime_in_seconds"),
            "streams_detected": list(set(streams))[:10]
        }
    except Exception as e:
        return False, {"error": str(e)}


def pg_check() -> tuple[bool, dict[str, Any]]:
    """Check TimescaleDB connectivity and hypertables."""
    try:
        import psycopg2
    except ImportError:
        return False, {"error": "psycopg2-binary not installed"}
    
    try:
        dsn = os.getenv("PG_DSN", "postgresql://postgres:postgres@localhost:5432/levibot")
        con = psycopg2.connect(dsn, connect_timeout=3)
        cur = con.cursor()
        
        # Check hypertables
        cur.execute("SELECT hypertable_name FROM timescaledb_information.hypertables;")
        hypertables = [x[0] for x in cur.fetchall()]
        
        # Check data
        tick_count = 0
        if "market_ticks" in hypertables:
            cur.execute("SELECT count(*) FROM market_ticks;")
            tick_count = cur.fetchone()[0]
        
        cur.close()
        con.close()
        
        return True, {
            "hypertables": hypertables,
            "market_ticks_count": tick_count
        }
    except Exception as e:
        return False, {"error": str(e)}


def main():
    """Run all health checks and generate report."""
    print("🔍 LEVIBOT Realtime Health Check\n")
    
    report: dict[str, Any] = {
        "api": {},
        "panel": {},
        "redis": {},
        "timescale": {},
        "sse": {},
        "paper": {}
    }
    
    # 1) Port checks
    print("1️⃣  Checking ports...")
    report["api"]["port"] = port_open("localhost", 8000)
    report["panel"]["port"] = port_open("localhost", 3001)
    print(f"   API (8000): {'✅' if report['api']['port'] else '❌'}")
    print(f"   Panel (3001): {'✅' if report['panel']['port'] else '❌'}")
    
    # 2) API health
    print("\n2️⃣  Checking API health...")
    try:
        r = get(f"{API}/healthz")
        report["api"]["healthz"] = (r.status_code == 200)
        if r.status_code == 200:
            report["api"]["healthz_data"] = r.json()
    except Exception as e:
        report["api"]["healthz"] = False
        report["api"]["healthz_error"] = str(e)
    print(f"   /healthz: {'✅' if report['api'].get('healthz') else '❌'}")
    
    # 3) Metrics endpoint
    print("\n3️⃣  Checking Prometheus metrics...")
    try:
        r = get(f"{API}/metrics")
        report["api"]["metrics"] = (r.status_code == 200)
        if r.status_code == 200:
            lines = r.text.split('\n')
            report["api"]["metrics_count"] = len([l for l in lines if l and not l.startswith('#')])
    except Exception as e:
        report["api"]["metrics"] = False
        report["api"]["metrics_error"] = str(e)
    print(f"   /metrics: {'✅' if report['api'].get('metrics') else '❌'}")
    
    # 4) SSE stream
    print("\n4️⃣  Checking SSE stream...")
    try:
        cnt = sse_read(f"{API}/stream/ticks", seconds=5)
        report["sse"]["ticks_count_5s"] = cnt
        report["sse"]["ok"] = cnt > 0
    except Exception as e:
        report["sse"]["ok"] = False
        report["sse"]["error"] = str(e)
    
    if report["sse"].get("ok"):
        print(f"   /stream/ticks: ✅ ({report['sse']['ticks_count_5s']} events in 5s)")
    elif report["sse"].get("ticks_count_5s") == -1:
        print("   /stream/ticks: ⚠️  (sseclient not installed, skipped)")
        report["sse"]["ok"] = None  # Unknown
    else:
        print("   /stream/ticks: ❌")
    
    # 5) Redis
    print("\n5️⃣  Checking Redis...")
    ok, info = redis_check()
    report["redis"]["ok"] = ok
    report["redis"]["info"] = info
    print(f"   Redis: {'✅' if ok else '❌'}")
    if ok:
        print(f"   Memory: {info.get('used_memory_human')}")
        print(f"   Streams: {info.get('streams_detected')}")
    
    # 6) TimescaleDB
    print("\n6️⃣  Checking TimescaleDB...")
    ok, info = pg_check()
    report["timescale"]["ok"] = ok
    report["timescale"]["info"] = info
    print(f"   TimescaleDB: {'✅' if ok else '❌'}")
    if ok:
        print(f"   Hypertables: {info.get('hypertables')}")
        print(f"   Ticks: {info.get('market_ticks_count')}")
    
    # 7) Paper trading
    print("\n7️⃣  Checking Paper Trading...")
    try:
        r = get(f"{API}/paper/portfolio")
        if r.status_code == 200:
            data = r.json()
            report["paper"]["equity"] = data.get("total_equity")
            report["paper"]["positions"] = data.get("open_positions")
            report["paper"]["ok"] = True
            print("   Paper Portfolio: ✅")
            print(f"   Equity: ${data.get('total_equity')}")
            print(f"   Positions: {data.get('open_positions')}")
        else:
            report["paper"]["ok"] = False
            print(f"   Paper Portfolio: ❌ (status {r.status_code})")
    except Exception as e:
        report["paper"]["ok"] = False
        report["paper"]["error"] = str(e)
        print("   Paper Portfolio: ❌")
    
    # 8) Panel health
    print("\n8️⃣  Checking Panel...")
    try:
        r = get(PANEL, timeout=2)
        report["panel"]["health"] = (r.status_code == 200)
        print(f"   Panel: {'✅' if report['panel']['health'] else '❌'}")
    except Exception as e:
        report["panel"]["health"] = False
        report["panel"]["error"] = str(e)
        print("   Panel: ❌")
    
    # Summary
    print("\n" + "="*50)
    ok_all = all([
        report["api"].get("port"),
        report["api"].get("healthz"),
        report["panel"].get("port"),
        report["redis"].get("ok"),
        report["timescale"].get("ok"),
    ])
    
    # SSE is optional (might not have sseclient or no data yet)
    if report["sse"].get("ok") is False:
        ok_all = False
    
    report["summary"] = {"ok": ok_all, "timestamp": time.time()}
    
    if ok_all:
        print("✅ ALL SYSTEMS OPERATIONAL")
    else:
        print("❌ SOME SYSTEMS HAVE ISSUES")
    
    print("="*50)
    print("\n📊 Full Report (JSON):\n")
    print(json.dumps(report, indent=2))
    
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())







