"""
Test data seeder for LeviBot
Generates realistic events for testing the Panel and API
"""

import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any


class DataSeeder:
    """Seeds test data into log files"""

    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = os.getenv("LOG_DIR", "/app/backend/data/logs")
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.test_files: list[Path] = []

    def _write_events(self, day: str, events: list[dict[str, Any]]):
        """Write events to a daily log file"""
        log_file = self.log_dir / f"{day}.jsonl"
        self.test_files.append(log_file)

        with open(log_file, "w") as f:
            for event in events:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")

        print(f"✅ {len(events)} events yazıldı: {log_file}")
        return log_file

    def _generate_signal_events(
        self, base_time: datetime, count: int = 10
    ) -> list[dict]:
        """Generate SIGNAL_SCORED events"""
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT"]
        sides = ["BUY", "SELL"]
        events = []

        for i in range(count):
            ts = (base_time + timedelta(minutes=i * 15)).isoformat() + "Z"
            symbol = random.choice(symbols)
            side = random.choice(sides)
            confidence = round(random.uniform(0.55, 0.95), 2)

            events.append(
                {
                    "ts": ts,
                    "event_type": "SIGNAL_SCORED",
                    "symbol": symbol,
                    "payload": {
                        "confidence": confidence,
                        "side": side,
                        "source": "ml_model",
                        "model_version": "v1.2.0",
                    },
                    "trace_id": f"sig-{i:03d}",
                }
            )

        return events

    def _generate_trade_events(self, base_time: datetime, count: int = 5) -> list[dict]:
        """Generate trading cycle events (OPEN -> CLOSE)"""
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        events = []

        for i in range(count):
            symbol = random.choice(symbols)
            trace_id = f"trade-{i:03d}"
            side = random.choice(["BUY", "SELL"])
            entry_price = random.uniform(1000, 50000)
            notional = random.uniform(50, 500)

            # AUTO_ROUTE_EXECUTED
            open_ts = (base_time + timedelta(hours=i * 2)).isoformat() + "Z"
            events.append(
                {
                    "ts": open_ts,
                    "event_type": "AUTO_ROUTE_EXECUTED",
                    "symbol": symbol,
                    "payload": {
                        "side": side,
                        "notional_usd": notional,
                        "confidence": round(random.uniform(0.7, 0.9), 2),
                    },
                    "trace_id": trace_id,
                }
            )

            # POSITION_CLOSED (after 1-4 hours)
            duration_sec = random.randint(3600, 14400)
            close_ts = (
                base_time + timedelta(hours=i * 2, seconds=duration_sec)
            ).isoformat() + "Z"

            # Random PnL (-20% to +30%)
            pnl_pct = random.uniform(-0.2, 0.3)
            pnl_usdt = round(notional * pnl_pct, 2)
            exit_price = entry_price * (1 + pnl_pct)

            events.append(
                {
                    "ts": close_ts,
                    "event_type": "POSITION_CLOSED",
                    "symbol": symbol,
                    "payload": {
                        "side": side,
                        "entry_price": round(entry_price, 2),
                        "exit_price": round(exit_price, 2),
                        "pnl_usdt": pnl_usdt,
                        "pnl_pct": round(pnl_pct * 100, 2),
                        "duration_sec": duration_sec,
                        "notional_usd": notional,
                    },
                    "trace_id": trace_id,
                }
            )

        return events

    def _generate_dex_events(self, base_time: datetime, count: int = 15) -> list[dict]:
        """Generate DEX quote events"""
        pairs = ["ETH/USDC", "BTC/USDC", "SOL/USDC"]
        events = []

        for i in range(count):
            ts = (base_time + timedelta(minutes=i * 5)).isoformat() + "Z"
            pair = random.choice(pairs)
            price = random.uniform(1000, 50000)

            events.append(
                {
                    "ts": ts,
                    "event_type": "DEX_QUOTE",
                    "symbol": pair,
                    "payload": {
                        "price": round(price, 2),
                        "liquidity": round(random.uniform(100000, 1000000), 2),
                        "chain": "ethereum",
                    },
                    "trace_id": None,
                }
            )

        return events

    def _generate_mev_events(self, base_time: datetime, count: int = 8) -> list[dict]:
        """Generate MEV arbitrage opportunity events"""
        events = []

        for i in range(count):
            ts = (base_time + timedelta(minutes=i * 20)).isoformat() + "Z"
            profit = round(random.uniform(10, 500), 2)

            events.append(
                {
                    "ts": ts,
                    "event_type": "MEV_ARB_OPP",
                    "symbol": None,
                    "payload": {
                        "path": ["USDC", "ETH", "WBTC", "USDC"],
                        "expected_profit_usd": profit,
                        "gas_cost_usd": round(profit * 0.1, 2),
                        "dexes": ["uniswap", "sushiswap", "curve"],
                    },
                    "trace_id": f"mev-{i:03d}",
                }
            )

        return events

    def _generate_telegram_events(
        self, base_time: datetime, count: int = 12
    ) -> list[dict]:
        """Generate Telegram signal events"""
        symbols = ["BTC", "ETH", "SOL", "BNB", "ADA"]
        events = []

        for i in range(count):
            ts = (base_time + timedelta(minutes=i * 10)).isoformat() + "Z"
            symbol = random.choice(symbols)

            # SIGNAL_INGEST
            events.append(
                {
                    "ts": ts,
                    "event_type": "SIGNAL_INGEST",
                    "symbol": None,
                    "payload": {
                        "source": "telegram",
                        "channel": f"trading_channel_{random.randint(1,5)}",
                        "text": f"BUY {symbol} tp {random.randint(40000, 70000)} sl {random.randint(30000, 45000)}",
                    },
                    "trace_id": f"tg-{i:03d}",
                }
            )

        return events

    def seed_day(self, day: str, full: bool = True) -> Path:
        """
        Seed a single day with test data

        Args:
            day: Date in YYYY-MM-DD format
            full: If True, generate all event types. If False, minimal set.
        """
        base_time = datetime.strptime(day, "%Y-%m-%d")
        events = []

        if full:
            # Comprehensive test data
            events.extend(self._generate_signal_events(base_time, count=10))
            events.extend(self._generate_trade_events(base_time, count=5))
            events.extend(self._generate_dex_events(base_time, count=15))
            events.extend(self._generate_mev_events(base_time, count=8))
            events.extend(self._generate_telegram_events(base_time, count=12))
        else:
            # Minimal test data
            events.extend(self._generate_signal_events(base_time, count=3))
            events.extend(self._generate_trade_events(base_time, count=2))

        # Sort by timestamp
        events.sort(key=lambda e: e["ts"])

        return self._write_events(day, events)

    def seed_range(self, start_day: str, days: int = 7, full: bool = True):
        """Seed multiple consecutive days"""
        start_dt = datetime.strptime(start_day, "%Y-%m-%d")

        for i in range(days):
            day = (start_dt + timedelta(days=i)).strftime("%Y-%m-%d")
            self.seed_day(day, full=full)

        print(f"\n✅ Toplam {days} gün test datası oluşturuldu")
        print(f"📊 Dosyalar: {self.log_dir}")

    def seed_today(self, full: bool = True):
        """Seed today's date with test data"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return self.seed_day(today, full=full)

    def cleanup(self):
        """Remove all test files created by this seeder"""
        removed = 0
        for file_path in self.test_files:
            if file_path.exists():
                file_path.unlink()
                removed += 1
                print(f"🗑️  Silindi: {file_path}")

        print(f"\n✅ {removed} test dosyası temizlendi")
        self.test_files.clear()

    def cleanup_all_test_data(self):
        """
        Remove ALL .jsonl files in log directory
        ⚠️  WARNING: This removes all log files, not just test data!
        """
        removed = 0
        for file_path in self.log_dir.glob("*.jsonl"):
            file_path.unlink()
            removed += 1
            print(f"🗑️  Silindi: {file_path}")

        # Also clean subdirectories
        for day_dir in self.log_dir.glob("20*"):
            if day_dir.is_dir():
                for file_path in day_dir.glob("*.jsonl"):
                    file_path.unlink()
                    removed += 1
                    print(f"🗑️  Silindi: {file_path}")

        print(f"\n⚠️  UYARI: {removed} dosya silindi!")


def seed_test_data_cli():
    """CLI entry point for seeding test data"""
    import sys

    seeder = DataSeeder()

    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == "today":
            seeder.seed_today(full=True)
        elif command == "week":
            today = datetime.utcnow()
            start = (today - timedelta(days=6)).strftime("%Y-%m-%d")
            seeder.seed_range(start, days=7, full=True)
        elif command == "minimal":
            seeder.seed_today(full=False)
        elif command == "cleanup":
            seeder.cleanup()
        elif command == "cleanup-all":
            confirm = input(
                "⚠️  TÜM log dosyaları silinecek! Onaylıyor musunuz? (yes/no): "
            )
            if confirm.lower() == "yes":
                seeder.cleanup_all_test_data()
            else:
                print("❌ İptal edildi")
        else:
            print(f"Bilinmeyen komut: {command}")
            print(
                "Kullanım: python seed_data.py [today|week|minimal|cleanup|cleanup-all]"
            )
    else:
        # Default: seed today
        seeder.seed_today(full=True)


if __name__ == "__main__":
    seed_test_data_cli()
