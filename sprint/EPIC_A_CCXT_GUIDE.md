# 📘 Epic-A: Real Data Ingestion (ccxt + Stream)

**Sprint:** S10 - The Real Deal  
**Epic ID:** A  
**Owner:** @siyahkare  
**Status:** 🚧 In Progress

---

## 🎯 Amaç

- ccxt ile **REST OHLCV** ve **orderbook snapshot**
- ccxt.pro (websocket) ile **ticker/trades akışı**
- **reconnect/backoff** + **time-sync & gap-fill**
- Engine'e **market data mapping**: `price, spread, vol, texts[], funding, oi`

---

## 🏗️ Mimari

```
backend/src/
  adapters/
    mexc_ccxt.py      # REST + WS adapter (ccxt/ccxt.pro)
  data/
    market_feeder.py  # WS akışı → engine md mapping
    gap_filler.py     # eksik minute barları tamamla (forward-fill)
  engine/
    engine.py         # md_queue injection için güncelleme
```

---

## 📊 Health & KPI

| Metrik | Hedef |
|--------|-------|
| Dropped messages | < %0.1 |
| p95 parse latency | < 5ms |
| 24h uptime | ≥ %99 |
| Reconnect recovery | < 10s |

---

## 📝 Implementation Tasks

### A1: REST OHLCV + Orderbook Snapshot

**File:** `backend/src/adapters/mexc_ccxt.py`

**Features:**
- ccxt.mexc() REST client with rate limiting
- `fetch_ohlcv(symbol, timeframe="1m", limit=1500)`
- `fetch_orderbook(symbol, limit=50)`
- Async executor wrapper for sync ccxt methods

**Test:** Verify 1500 bars fetched for BTC/USDT

### A2: WebSocket Ticker/Trades + Reconnect

**File:** `backend/src/adapters/mexc_ccxt.py`

**Features:**
- ccxt.pro WebSocket client
- `stream_ticker(symbol)` → async iterator
- `stream_trades(symbol)` → async iterator
- Exponential backoff on disconnect (1s baseline)
- Exception handling with auto-reconnect

**Test:** 5-minute continuous stream without crash

### A3: Feeder → Engine MD Mapping

**File:** `backend/src/data/market_feeder.py`

**Features:**
- Bootstrap: fetch 1500 bars + gap-fill
- Stream aggregation: ticker → md dict
- MD format: `{symbol, price, spread, vol, texts, funding, oi}`
- Callback-based injection: `on_md(md)`

**Test:** MD dict contains all required fields

### A4: Gap-Fill + Time-Sync

**File:** `backend/src/data/gap_filler.py`

**Features:**
- Detect missing minute bars (>60s gap)
- Forward-fill OHLC from last close
- Volume = 0 for synthetic bars
- NTP time sync check (optional)

**Test:** 3-minute gap produces 2 synthetic bars

---

## 🔧 Implementation Code

### 1) MEXC Adapter — `backend/src/adapters/mexc_ccxt.py`

```python
import asyncio
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List

import ccxt
import ccxt.pro as ccxtpro


class MexcAdapter:
    """MEXC exchange adapter using ccxt for REST and ccxt.pro for WebSocket."""

    def __init__(self, symbols: list[str], rate_limit: bool = True):
        self.rest = ccxt.mexc({"enableRateLimit": rate_limit})
        self.ws = ccxtpro.mexc()
        self.symbols = symbols

    async def fetch_ohlcv(
        self, symbol: str, timeframe: str = "1m", limit: int = 1500
    ) -> list[list]:
        """Fetch OHLCV bars via REST API."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.rest.fetch_ohlcv, symbol, timeframe, None, limit
        )

    async def fetch_orderbook(self, symbol: str, limit: int = 50) -> Dict[str, Any]:
        """Fetch orderbook snapshot via REST API."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.rest.fetch_order_book, symbol, limit
        )

    async def stream_trades(self, symbol: str) -> AsyncIterator[Dict[str, Any]]:
        """Stream trades via WebSocket with auto-reconnect."""
        while True:
            try:
                trades = await self.ws.watch_trades(symbol)
                for t in trades:
                    yield {
                        "ts": int(t["timestamp"]),
                        "price": float(t["price"]),
                        "amount": float(t["amount"]),
                        "side": t.get("side", ""),
                    }
            except Exception:
                await asyncio.sleep(1.0)  # reconnect/backoff

    async def stream_ticker(self, symbol: str) -> AsyncIterator[Dict[str, Any]]:
        """Stream ticker via WebSocket with auto-reconnect."""
        while True:
            try:
                tk = await self.ws.watch_ticker(symbol)
                yield {
                    "ts": int(datetime.now(timezone.utc).timestamp() * 1000),
                    "bid": float(tk.get("bid", 0) or 0),
                    "ask": float(tk.get("ask", 0) or 0),
                    "last": float(tk.get("last", 0) or 0),
                    "spread": float(tk.get("ask", 0) or 0)
                    - float(tk.get("bid", 0) or 0),
                    "volume": float(tk.get("baseVolume", 0) or 0),
                }
            except Exception:
                await asyncio.sleep(1.0)

    async def close(self):
        """Close WebSocket connection."""
        await self.ws.close()
```

### 2) Gap Filler — `backend/src/data/gap_filler.py`

```python
from datetime import datetime, timezone


def minute_floor(ts_ms: int) -> int:
    """Floor timestamp to minute boundary."""
    dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
    floored = dt.replace(second=0, microsecond=0)
    return int(floored.timestamp() * 1000)


def fill_minute_bars(ohlcv: list[list]) -> list[list]:
    """
    Fill missing minute bars with forward-fill from last close.
    
    Args:
        ohlcv: [[ms, o, h, l, c, v], ...] sorted ascending by timestamp
        
    Returns:
        Filled OHLCV with synthetic bars for gaps > 1 minute
    """
    if not ohlcv:
        return ohlcv

    filled = []
    i = 0
    cur = ohlcv[0]

    while i < len(ohlcv) - 1:
        nxt = ohlcv[i + 1]
        filled.append(cur)

        # Check for gaps > 1 minute
        dt = nxt[0] - cur[0]
        if dt > 60_000:
            steps = dt // 60_000 - 1
            for s in range(int(steps)):
                ts = cur[0] + 60_000 * (s + 1)
                o = h = l = c = cur[4]  # Forward-fill from last close
                v = 0.0  # Zero volume for synthetic bars
                filled.append([ts, o, h, l, c, v])

        cur = nxt
        i += 1

    filled.append(ohlcv[-1])
    return filled
```

### 3) Market Feeder — `backend/src/data/market_feeder.py`

```python
import asyncio
from typing import Any, Callable, Dict, List, Optional

from ..adapters.mexc_ccxt import MexcAdapter
from .gap_filler import fill_minute_bars


class MarketFeeder:
    """Feeds market data to trading engines via callback."""

    def __init__(self, symbols: list[str], adapter: Optional[MexcAdapter] = None):
        self.symbols = symbols
        self.adapter = adapter or MexcAdapter(symbols)

    async def bootstrap_bars(self, symbol: str) -> list[list]:
        """Fetch and gap-fill initial OHLCV bars."""
        raw = await self.adapter.fetch_ohlcv(symbol, "1m", 1500)
        return fill_minute_bars(sorted(raw, key=lambda r: r[0]))

    async def stream_symbol(
        self, symbol: str, on_md: Callable[[Dict[str, Any]], None]
    ):
        """Stream market data for a single symbol."""
        # Bootstrap with historical bars
        bars = await self.bootstrap_bars(symbol)
        last = bars[-1][4] if bars else 0.0

        async def run_ticker():
            async for tk in self.adapter.stream_ticker(symbol):
                md = {
                    "symbol": symbol,
                    "price": tk["last"] or last,
                    "spread": tk["spread"],
                    "vol": tk["volume"],
                    "texts": [],  # Placeholder for news/tweets
                    "funding": 0.0,  # Placeholder for funding rate
                    "oi": 0.0,  # Placeholder for open interest
                }
                await on_md(md)

        async def run_trades():
            async for tr in self.adapter.stream_trades(symbol):
                pass  # Optional: aggregate trade-based volume/OI

        await asyncio.gather(run_ticker(), run_trades())

    async def run(self, on_md: Callable[[Dict[str, Any]], None]):
        """Run market data streams for all symbols."""
        await asyncio.gather(
            *(self.stream_symbol(s, on_md) for s in self.symbols)
        )

    async def close(self):
        """Close adapter connections."""
        await self.adapter.close()
```

---

## 🧪 Tests

### Test 1: Gap Filler — `backend/tests/test_gap_filler.py`

```python
from backend.src.data.gap_filler import fill_minute_bars


def test_fill_bars_inserts_missing_minutes():
    """Test that gap filler inserts synthetic bars for missing minutes."""
    base = 1_700_000_000_000
    # 3-minute gap between bars
    ohlcv = [
        [base, 1, 2, 0.5, 1.5, 10],
        [base + 3 * 60_000, 1.6, 2, 1.2, 1.8, 12],
    ]
    out = fill_minute_bars(ohlcv)
    
    # Should have: base, +1m (synthetic), +2m (synthetic), +3m
    assert len(out) == 4
    assert out[1][0] == base + 60_000
    assert out[2][0] == base + 2 * 60_000
    assert out[1][4] == 1.5  # Forward-fill from last close
    assert out[2][4] == 1.5
    assert out[1][5] == 0.0  # Zero volume
```

### Test 2: MEXC Adapter Signatures — `backend/tests/test_mexc_adapter.py`

```python
import pytest

from backend.src.adapters.mexc_ccxt import MexcAdapter


@pytest.mark.asyncio
async def test_adapter_has_required_methods():
    """Verify adapter has required methods (no network calls)."""
    adapter = MexcAdapter(["BTC/USDT"])
    
    assert hasattr(adapter, "fetch_ohlcv")
    assert hasattr(adapter, "fetch_orderbook")
    assert hasattr(adapter, "stream_ticker")
    assert hasattr(adapter, "stream_trades")
    assert hasattr(adapter, "close")
```

### Test 3: Market Feeder Bootstrap — `backend/tests/test_market_feeder.py`

```python
import pytest

from backend.src.adapters.mexc_ccxt import MexcAdapter
from backend.src.data.market_feeder import MarketFeeder


class DummyAdapter(MexcAdapter):
    """Mock adapter for testing without network calls."""

    def __init__(self):
        pass  # Skip parent init

    async def fetch_ohlcv(self, symbol, timeframe="1m", limit=1500):
        base = 1_700_000_000_000
        return [
            [base, 1, 2, 0.5, 1.0, 10],
            [base + 3 * 60_000, 1, 2, 0.5, 1.1, 10],
        ]

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_bootstrap_fills_gaps():
    """Test that bootstrap fills gaps in OHLCV data."""
    feeder = MarketFeeder(["BTC/USDT"], adapter=DummyAdapter())
    bars = await feeder.bootstrap_bars("BTC/USDT")
    
    # Should have 4 bars: original 2 + 2 synthetic
    assert len(bars) == 4
```

---

## ⚡ Quickstart

### 1. Install Dependencies

```bash
cd /Users/onur/levibot/backend
source venv/bin/activate
pip install ccxt ccxt.pro
```

### 2. Run Local Test (Mock-Free)

```bash
python - <<'PY'
import asyncio
from backend.src.data.market_feeder import MarketFeeder

async def on_md(md):
    if md.get("price"):
        print(f"{md['symbol']}: ${md['price']:.2f} | spread: {md['spread']:.4f}")

async def main():
    feeder = MarketFeeder(["BTC/USDT"])
    try:
        await asyncio.wait_for(feeder.run(on_md), timeout=10.0)
    except asyncio.TimeoutError:
        await feeder.close()

asyncio.run(main())
PY
```

### 3. Run Tests

```bash
PYTHONPATH=backend pytest backend/tests/test_gap_filler.py -v
PYTHONPATH=backend pytest backend/tests/test_mexc_adapter.py -v
PYTHONPATH=backend pytest backend/tests/test_market_feeder.py -v
```

---

## 🔗 Engine Integration

### Engine MD Queue Injection

Update `backend/src/engine/engine.py`:

```python
# In __init__:
self._md_queue: asyncio.Queue = asyncio.Queue(maxsize=100)

# External injection (from manager):
# await feeder.run(lambda md: engine._md_queue.put_nowait(md) if md['symbol'] == engine.symbol else None)

async def _get_md(self) -> Dict[str, Any]:
    try:
        md = await asyncio.wait_for(self._md_queue.get(), timeout=1.0)
        return md
    except asyncio.TimeoutError:
        return {"price": None, "spread": None, "vol": 0.0, "texts": []}
```

---

## ✅ Definition of Done (Epic-A)

- [ ] REST OHLCV + orderbook snapshot working
- [ ] WS ticker/trades stream stable with reconnect/backoff
- [ ] Gap-fill correctly inserts synthetic bars (forward-fill)
- [ ] Engine MD mapping functional (price/spread/vol/texts/funding/oi)
- [ ] 24h smoke test: dropped < %0.1, p95 parse < 5ms
- [ ] All tests passing (gap_filler, adapter, feeder)
- [ ] Requirements updated with ccxt dependencies

---

## 📦 Required Files

```
backend/src/adapters/mexc_ccxt.py          ✅
backend/src/data/gap_filler.py             ✅
backend/src/data/market_feeder.py          ✅
backend/tests/test_gap_filler.py           ✅
backend/tests/test_mexc_adapter.py         ✅
backend/tests/test_market_feeder.py        ✅
backend/requirements.txt                   (update: ccxt>=4.0.0)
```

---

**Status:** 🚧 Ready for implementation  
**Next Steps:** Create skeleton files → Run tests → Integrate with EngineManager  
**Owner:** @siyahkare

