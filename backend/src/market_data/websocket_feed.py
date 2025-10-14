"""
WebSocket Market Data Feed
Real-time price updates from exchanges (MEXC stub for now)
"""
import asyncio
import time
from collections.abc import Callable

import numpy as np


class MarketDataFeed:
    """
    Market data feed using WebSocket (stub implementation).
    
    In production, this would connect to MEXC/Binance WebSocket APIs.
    For now, it provides mock real-time data with realistic characteristics.
    """
    
    def __init__(self, symbol: str = "BTCUSDT", base_price: float = 50000.0):
        self.symbol = symbol
        self.base_price = base_price
        self.current_price = base_price
        self.running = False
        self.callbacks: list[Callable] = []
        self._task = None
    
    def subscribe(self, callback: Callable):
        """Subscribe to price updates"""
        self.callbacks.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from price updates"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    async def start(self):
        """Start the WebSocket feed"""
        if self.running:
            return
        
        self.running = True
        self._task = asyncio.create_task(self._feed_loop())
    
    async def stop(self):
        """Stop the WebSocket feed"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    async def _feed_loop(self):
        """
        Main feed loop - simulates WebSocket ticks.
        
        In production, this would:
        1. Connect to MEXC WebSocket
        2. Subscribe to ticker channel
        3. Parse incoming messages
        4. Emit price updates
        
        Stub behavior:
        - 4 Hz update rate (250ms)
        - Realistic price movement (random walk)
        - Bid/ask spread simulation
        """
        while self.running:
            try:
                # Simulate price movement (random walk with slight trend)
                change = np.random.randn() * 10 + 0.5  # Slight upward bias
                self.current_price += change
                
                # Ensure price doesn't drift too far
                if abs(self.current_price - self.base_price) > 1000:
                    self.current_price = self.base_price
                
                # Calculate bid/ask with realistic spread (0.01%)
                spread_bps = 1.0  # 1 basis point
                spread = self.current_price * (spread_bps / 10000)
                bid = self.current_price - spread / 2
                ask = self.current_price + spread / 2
                
                # Create tick data
                tick = {
                    "symbol": self.symbol,
                    "timestamp": time.time(),
                    "price": self.current_price,
                    "bid": bid,
                    "ask": ask,
                    "volume": np.random.uniform(0.1, 2.0),  # Mock volume
                }
                
                # Emit to all subscribers
                for callback in self.callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(tick)
                        else:
                            callback(tick)
                    except Exception as e:
                        print(f"⚠️ Callback error: {e}")
                
                # 4 Hz tick rate
                await asyncio.sleep(0.25)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"⚠️ Feed loop error: {e}")
                await asyncio.sleep(1.0)


class RealMEXCFeed(MarketDataFeed):
    """
    Real MEXC WebSocket feed (placeholder for future implementation).
    
    To implement:
    1. Install websockets library
    2. Connect to wss://wbs.mexc.com/ws
    3. Subscribe to spot@public.deals.v3.api@{symbol}
    4. Parse JSON messages
    5. Emit price updates
    """
    
    async def _feed_loop(self):
        """
        Real MEXC WebSocket connection.
        
        Example:
            import websockets
            
            uri = "wss://wbs.mexc.com/ws"
            async with websockets.connect(uri) as ws:
                subscribe_msg = {
                    "method": "SUBSCRIPTION",
                    "params": [f"spot@public.deals.v3.api@{self.symbol}"]
                }
                await ws.send(json.dumps(subscribe_msg))
                
                while self.running:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    # Parse and emit tick...
        """
        # For now, fallback to mock
        await super()._feed_loop()


# Global feed instances
_FEEDS: dict[str, MarketDataFeed] = {}


def get_feed(symbol: str = "BTCUSDT", real: bool = False) -> MarketDataFeed:
    """
    Get or create market data feed for symbol.
    
    Args:
        symbol: Trading symbol
        real: Use real WebSocket (placeholder, uses mock for now)
    
    Returns:
        MarketDataFeed instance
    """
    if symbol not in _FEEDS:
        if real:
            _FEEDS[symbol] = RealMEXCFeed(symbol)
        else:
            _FEEDS[symbol] = MarketDataFeed(symbol)
    
    return _FEEDS[symbol]


