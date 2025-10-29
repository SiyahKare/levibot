"""
Market Data Service - Sürekli MEXC'den data toplar ve veritabanına kaydeder.
"""

import asyncio
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from ..adapters.mexc_ccxt import MexcAdapter
from ..data.feature_store import minute_features, to_parquet


class MarketDataService:
    """Sürekli market data toplama ve kaydetme servisi."""

    def __init__(self, symbols: list[str], interval_seconds: int = 60):
        self.symbols = symbols
        self.interval_seconds = interval_seconds
        self.adapter = MexcAdapter(symbols)
        self.running = False
        self._task: asyncio.Task | None = None

    async def start(self):
        """Servisi başlat."""
        if self.running:
            print("⚠️ Market data service already running")
            return

        self.running = True
        self._task = asyncio.create_task(self._run_loop())
        print(f"🚀 Market data service started for {len(self.symbols)} symbols")

    async def stop(self):
        """Servisi durdur."""
        if not self.running:
            return

        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        await self.adapter.close()
        print("🛑 Market data service stopped")

    async def _run_loop(self):
        """Ana data toplama loop'u."""
        while self.running:
            try:
                await self._collect_and_store_data()
                await asyncio.sleep(self.interval_seconds)
            except Exception as e:
                print(f"❌ Market data collection error: {e}")
                await asyncio.sleep(5)  # Hata durumunda kısa bekle

    async def _collect_and_store_data(self):
        """Tüm symbol'ler için data topla ve kaydet."""
        for symbol in self.symbols:
            try:
                await self._collect_symbol_data(symbol)
            except Exception as e:
                print(f"❌ Error collecting data for {symbol}: {e}")

    async def _collect_symbol_data(self, symbol: str):
        """Tek symbol için data topla ve kaydet."""
        try:
            # OHLCV data al
            bars = await self.adapter.fetch_ohlcv(symbol, "1m", 100)
            if not bars:
                print(f"⚠️ No bars received for {symbol}")
                return

            # DataFrame'e çevir
            df = pd.DataFrame(
                bars, columns=["ts", "open", "high", "low", "close", "volume"]
            )
            df["symbol"] = symbol.replace("/", "").replace(
                "-", ""
            )  # BTC/USDT -> BTCUSDT

            # Timestamp'i düzelt (ms -> s)
            df["ts"] = df["ts"] // 1000

            # Features hesapla
            features_df = minute_features(df, horizon=5)

            # Parquet'e kaydet
            output_path = to_parquet(
                features_df, "backend/data/feature_store", symbol.replace("/", "")
            )

            # Log
            latest_price = df["close"].iloc[-1]
            latest_ts = datetime.fromtimestamp(df["ts"].iloc[-1], UTC)
            print(
                f"📊 {symbol}: ${latest_price:.2f} at {latest_ts.strftime('%H:%M:%S')} -> {output_path}"
            )

        except Exception as e:
            print(f"❌ Error processing {symbol}: {e}")

    async def get_latest_data(
        self, symbol: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Son N bar'ı getir."""
        try:
            bars = await self.adapter.fetch_ohlcv(symbol, "1m", limit)
            return [
                {
                    "ts": bar[0] // 1000,  # ms -> s
                    "open": bar[1],
                    "high": bar[2],
                    "low": bar[3],
                    "close": bar[4],
                    "volume": bar[5],
                }
                for bar in bars
            ]
        except Exception as e:
            print(f"❌ Error fetching latest data for {symbol}: {e}")
            return []


# Global service instance
_market_data_service: MarketDataService | None = None


async def get_market_data_service() -> MarketDataService:
    """Market data service singleton'ını al."""
    global _market_data_service
    if _market_data_service is None:
        _market_data_service = MarketDataService(
            symbols=["BTC/USDT", "ETH/USDT", "SOL/USDT"], interval_seconds=60
        )
    return _market_data_service


async def start_market_data_service():
    """Market data service'i başlat."""
    service = await get_market_data_service()
    await service.start()


async def stop_market_data_service():
    """Market data service'i durdur."""
    global _market_data_service
    if _market_data_service:
        await _market_data_service.stop()
        _market_data_service = None
