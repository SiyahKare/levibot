#!/usr/bin/env python3
"""
MEXC Feed Diagnosis Tool
──────────────────────────────────────────
Check tick prices, feed health, and trade entries.

Usage:
    python scripts/diagnose_feed.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
    """Get TimescaleDB connection"""
    return psycopg2.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        database="levibot"
    )


def check_recent_ticks(symbol: str = "BTCUSDT", limit: int = 20):
    """Check recent tick data"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print(f"\n📊 Recent Ticks for {symbol} (last {limit}):")
    print("─" * 80)
    
    cur.execute("""
        SELECT ts, price, bid, ask, size, source, latency_ms
        FROM market_ticks
        WHERE symbol = %s
        ORDER BY ts DESC
        LIMIT %s
    """, (symbol, limit))
    
    rows = cur.fetchall()
    
    if not rows:
        print(f"❌ No ticks found for {symbol}")
        cur.close()
        conn.close()
        return
    
    for row in rows:
        ts = row["ts"]
        price = row["price"]
        bid = row["bid"]
        ask = row["ask"]
        size = row["size"]
        source = row["source"]
        latency_ms = row.get("latency_ms", 0) or 0
        
        spread = ask - bid if ask and bid else 0
        spread_bps = (spread / price * 10000) if price > 0 else 0
        
        print(f"{ts} | ${price:>10,.2f} | Bid: ${bid:>10,.2f} | Ask: ${ask:>10,.2f} | "
              f"Spread: {spread_bps:>6.2f} bps | Size: {size:>8.4f} | "
              f"Source: {source:>8} | Latency: {latency_ms:>4.0f}ms")
    
    cur.close()
    conn.close()


def check_price_stats(symbol: str = "BTCUSDT"):
    """Check price statistics"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print(f"\n📈 Price Statistics for {symbol} (24h):")
    print("─" * 80)
    
    cur.execute("""
        SELECT
            COUNT(*) as tick_count,
            MIN(price) as min_price,
            MAX(price) as max_price,
            AVG(price) as avg_price,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median_price,
            STDDEV(price) as std_price
        FROM market_ticks
        WHERE symbol = %s
          AND ts > NOW() - INTERVAL '24 hours'
    """, (symbol,))
    
    stats = cur.fetchone()
    
    if not stats or not stats["tick_count"]:
        print(f"❌ No data for {symbol} in last 24h")
        cur.close()
        conn.close()
        return
    
    print(f"Tick Count: {stats['tick_count']:,}")
    print(f"Min Price:  ${stats['min_price']:,.2f}")
    print(f"Max Price:  ${stats['max_price']:,.2f}")
    print(f"Avg Price:  ${stats['avg_price']:,.2f}")
    print(f"Median:     ${stats['median_price']:,.2f}")
    print(f"Std Dev:    ${stats['std_price']:,.2f}")
    
    # Check for anomalies
    median = stats['median_price']
    min_price = stats['min_price']
    max_price = stats['max_price']
    
    min_deviation = abs(min_price - median) / median
    max_deviation = abs(max_price - median) / median
    
    print("\n⚠️  Anomaly Check:")
    if min_deviation > 0.5:
        print(f"   ❌ Min price {min_deviation*100:.1f}% below median (>50% deviation!)")
    else:
        print(f"   ✅ Min price {min_deviation*100:.1f}% below median")
    
    if max_deviation > 0.5:
        print(f"   ❌ Max price {max_deviation*100:.1f}% above median (>50% deviation!)")
    else:
        print(f"   ✅ Max price {max_deviation*100:.1f}% above median")
    
    cur.close()
    conn.close()


def check_recent_trades(limit: int = 10):
    """Check recent trades from LSE/Day/Swing engines"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print(f"\n🔄 Recent Trades (last {limit}):")
    print("─" * 80)
    
    cur.execute("""
        SELECT ts, strategy, symbol, side, qty, price, pnl, reason
        FROM trades
        ORDER BY ts DESC
        LIMIT %s
    """, (limit,))
    
    rows = cur.fetchall()
    
    if not rows:
        print("❌ No trades found")
        cur.close()
        conn.close()
        return
    
    for row in rows:
        ts = row["ts"]
        strategy = row["strategy"]
        symbol = row["symbol"]
        side = row["side"]
        qty = row["qty"]
        price = row["price"]
        pnl = row.get("pnl", 0) or 0
        reason = row.get("reason", "-")
        
        print(f"{ts} | {strategy:>6} | {symbol:>10} | {side:>4} | "
              f"Qty: {qty:>8.4f} | Price: ${price:>10,.2f} | "
              f"PnL: ${pnl:>8,.2f} | Reason: {reason}")
    
    cur.close()
    conn.close()


def check_feed_source():
    """Check feed source distribution"""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    print("\n🔌 Feed Source Distribution (24h):")
    print("─" * 80)
    
    cur.execute("""
        SELECT source, COUNT(*) as count
        FROM market_ticks
        WHERE ts > NOW() - INTERVAL '24 hours'
        GROUP BY source
        ORDER BY count DESC
    """)
    
    rows = cur.fetchall()
    
    if not rows:
        print("❌ No ticks in last 24h")
        cur.close()
        conn.close()
        return
    
    total = sum(row["count"] for row in rows)
    
    for row in rows:
        source = row["source"]
        count = row["count"]
        pct = count / total * 100
        print(f"{source:>12}: {count:>10,} ticks ({pct:>5.1f}%)")
    
    cur.close()
    conn.close()


def main():
    print("=" * 80)
    print("🔍 MEXC FEED DIAGNOSIS")
    print("=" * 80)
    
    # Check feed source
    check_feed_source()
    
    # Check recent ticks
    check_recent_ticks("BTCUSDT", limit=20)
    
    # Check price stats
    check_price_stats("BTCUSDT")
    
    # Check recent trades
    check_recent_trades(limit=10)
    
    print("\n" + "=" * 80)
    print("✅ DIAGNOSIS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()


