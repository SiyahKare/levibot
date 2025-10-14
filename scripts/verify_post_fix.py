#!/usr/bin/env python3
"""
Post-Fix Validation Script
Doğrular: Panel proxy, API health, SSE akışı, Telegram status, Paper SELL, SWR refresh
"""
import json
import os
import time

import requests

API = os.getenv("API_URL", "http://localhost:8000")
PANEL = os.getenv("PANEL_URL", "http://localhost:3001")


def ok(status):
    return 200 <= status < 300


def panel_health():
    """Panel root health check"""
    try:
        r = requests.get(f"{PANEL}/", timeout=3)
        return {"ok": ok(r.status_code), "status": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def api_health():
    """API healthz endpoint check"""
    try:
        r = requests.get(f"{API}/healthz", timeout=3)
        return {"ok": ok(r.status_code), "status": r.status_code, "body": r.json() if ok(r.status_code) else {}}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def sse_ticks(seconds=5):
    """SSE /stream/ticks gerçek zamanlı akış testi"""
    try:
        # sseclient-py gerektiriyor, yoksa basit line-by-line okuma
        try:
            import sseclient
            r = requests.get(f"{API}/stream/ticks", stream=True, timeout=seconds + 2)
            client = sseclient.SSEClient(r)
            start = time.time()
            cnt = 0
            for e in client.events():
                cnt += 1
                if time.time() - start > seconds:
                    break
            return {"ok": cnt > 0, "count_5s": cnt}
        except ImportError:
            # Fallback: basit stream okuma
            r = requests.get(f"{API}/stream/ticks", stream=True, timeout=seconds + 2)
            start = time.time()
            cnt = 0
            for line in r.iter_lines():
                if line and line.startswith(b"data:"):
                    cnt += 1
                if time.time() - start > seconds:
                    break
            return {"ok": cnt > 0, "count_5s": cnt}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def telegram_status():
    """/telegram/status endpoint şema kontrolü"""
    try:
        r = requests.get(f"{API}/telegram/status", timeout=4)
        data = r.json() if ok(r.status_code) else {}
        # Şema: {"ok": bool, "bot_configured": bool, "alert_chat_configured": bool, "connection": str}
        schema_ok = (
            isinstance(data, dict)
            and "ok" in data
            and "bot_configured" in data
            and "connection" in data
        )
        return {
            "ok": ok(r.status_code) and schema_ok,
            "status": r.status_code,
            "data": data,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def paper_sell_smoke():
    """
    SELL payload testi: önce BUY, sonra SELL yaparak tam akış kontrolü
    """
    symbol = "BTCUSDT"
    try:
        # 1) Önce BUY pozisyonu aç
        buy_payload = {"symbol": symbol, "side": "buy", "notional_usd": 50.0}
        r_buy = requests.post(f"{API}/paper/order", json=buy_payload, timeout=5)
        if not ok(r_buy.status_code):
            return {"ok": False, "status": r_buy.status_code, "resp": {"error": "BUY failed"}}
        
        # 2) Sonra SELL ile kapat
        sell_payload = {"symbol": symbol, "side": "sell", "notional_usd": 0}  # notional irrelevant for SELL
        r_sell = requests.post(f"{API}/paper/order", json=sell_payload, timeout=5)
        ok1 = ok(r_sell.status_code)
        j = r_sell.json() if ok1 else {}
        
        # Backend'de side "sell" echo olmalı
        sell_echo = j.get("side") == "sell"
        return {"ok": ok1 and sell_echo, "status": r_sell.status_code, "resp": j}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def swr_refresh_probe():
    """
    SWR auto-refresh testi: Aynı endpoint'i 11sn arayla çağırıp içerik değişimini kontrol eder
    Panel'de useSWR refreshInterval: 10000 varsa bu farkı görebiliriz
    """
    url = f"{API}/analytics/stats?days=1"
    out = {}
    try:
        a = requests.get(url, timeout=4)
        time.sleep(11)  # SWR refresh window'dan biraz fazla
        b = requests.get(url, timeout=4)
        out["first_ok"] = ok(a.status_code)
        out["second_ok"] = ok(b.status_code)
        out["changed"] = a.text != b.text
        out["hint"] = "changed=True SWR refresh çalışıyor demektir"
        out["ok"] = out["first_ok"] and out["second_ok"]
    except Exception as e:
        out = {"ok": False, "error": str(e)}
    return out


def main():
    print("🔍 Panel Post-Fix Doğrulama Başlıyor...\n")
    
    report = {
        "panel": panel_health(),
        "api": api_health(),
        "sse": sse_ticks(5),
        "telegram": telegram_status(),
        "paper_sell": paper_sell_smoke(),
        "swr": swr_refresh_probe(),
    }
    
    # Genel özet
    report["summary"] = {
        "ok": all(v.get("ok") for k, v in report.items() if k != "summary"),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    print(json.dumps(report, indent=2))
    
    # Exit code
    exit(0 if report["summary"]["ok"] else 1)


if __name__ == "__main__":
    main()

