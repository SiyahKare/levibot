#!/usr/bin/env python3
"""
Clean Anomalous Ticks from TimescaleDB
──────────────────────────────────────────
Removes outlier ticks (±2x median band) to prevent bad entries.

Usage:
    python scripts/clean_anomalous_ticks.py --symbol BTCUSDT --dry-run
    python scripts/clean_anomalous_ticks.py --symbol BTCUSDT --execute
    python scripts/clean_anomalous_ticks.py --all-symbols --execute
"""

import argparse
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


def clean_anomalous_ticks(symbol: str, dry_run: bool = True):
    """
    Clean anomalous ticks for a symbol.
    
    Strategy:
        1. Calculate 24h median price
        2. Delete ticks outside ±2x median band
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    # Get 24h median
    cur.execute("""
        SELECT PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) AS p50
        FROM market_ticks
        WHERE symbol = %s
          AND ts > NOW() - INTERVAL '24 hours'
    """, (symbol,))
    
    result = cur.fetchone()
    if not result or not result["p50"]:
        print(f"❌ No data found for {symbol} in last 24h")
        return
    
    median = float(result["p50"])
    lower_bound = median * 0.5  # -50%
    upper_bound = median * 2.0  # +100%
    
    print(f"📊 {symbol} Statistics:")
    print(f"   Median (24h): ${median:,.2f}")
    print(f"   Band: ${lower_bound:,.2f} - ${upper_bound:,.2f}")
    
    # Count anomalies
    cur.execute("""
        SELECT COUNT(*) as count
        FROM market_ticks
        WHERE symbol = %s
          AND (price > %s OR price < %s)
    """, (symbol, upper_bound, lower_bound))
    
    anomaly_count = cur.fetchone()["count"]
    print(f"   Anomalies found: {anomaly_count}")
    
    if anomaly_count == 0:
        print(f"✅ No anomalies to clean for {symbol}")
        cur.close()
        conn.close()
        return
    
    if dry_run:
        print(f"🔍 DRY RUN - Would delete {anomaly_count} anomalous ticks")
    else:
        # Delete anomalies
        cur.execute("""
            DELETE FROM market_ticks
            WHERE symbol = %s
              AND (price > %s OR price < %s)
        """, (symbol, upper_bound, lower_bound))
        
        conn.commit()
        print(f"✅ Deleted {anomaly_count} anomalous ticks for {symbol}")
    
    cur.close()
    conn.close()


def clean_all_symbols(dry_run: bool = True):
    """Clean anomalous ticks for all symbols"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get unique symbols
    cur.execute("""
        SELECT DISTINCT symbol
        FROM market_ticks
        WHERE ts > NOW() - INTERVAL '24 hours'
    """)
    
    symbols = [row[0] for row in cur.fetchall()]
    cur.close()
    conn.close()
    
    print(f"Found {len(symbols)} symbols: {symbols}")
    print()
    
    for symbol in symbols:
        clean_anomalous_ticks(symbol, dry_run=dry_run)
        print()


def main():
    parser = argparse.ArgumentParser(description="Clean anomalous ticks from TimescaleDB")
    parser.add_argument("--symbol", type=str, help="Symbol to clean (e.g., BTCUSDT)")
    parser.add_argument("--all-symbols", action="store_true", help="Clean all symbols")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Dry run (default)")
    parser.add_argument("--execute", action="store_true", help="Execute deletion")
    
    args = parser.parse_args()
    
    if not args.symbol and not args.all_symbols:
        print("❌ Specify --symbol SYMBOL or --all-symbols")
        sys.exit(1)
    
    dry_run = not args.execute
    
    if dry_run:
        print("🔍 DRY RUN MODE - No data will be deleted")
        print("   Use --execute to actually delete anomalies")
        print()
    else:
        print("⚠️  EXECUTE MODE - Data will be deleted!")
        print()
    
    if args.all_symbols:
        clean_all_symbols(dry_run=dry_run)
    else:
        clean_anomalous_ticks(args.symbol, dry_run=dry_run)


if __name__ == "__main__":
    main()


