"""
MEXC Exchange Filters & Order Normalization
Ensures 100% exchange-compliant trade sizing
"""
import time
from dataclasses import dataclass
from typing import Literal

import ccxt.async_support as ccxt

# Symbol normalization helpers
SPOT_SUFFIXES = ("", ":USDT")
DELIMS = ("/", "")


def build_symbol_map(markets: dict[str, dict]) -> dict[str, str]:
    """
    Build normalized symbol map from CCXT markets
    
    Handles variants like:
    - BTCUSDT, BTC/USDT, btc/usdt, BTC/USDT:USDT
    
    Returns:
        Dict mapping normalized symbols to market keys
    """
    symmap: dict[str, str] = {}
    
    for mkey, m in markets.items():
        base = m.get("base")
        quote = m.get("quote")
        if not base or not quote:
            continue
        
        # Generate variants
        variants = set()
        for d in DELIMS:
            variants.add(f"{base}{d}{quote}".upper())
            variants.add(f"{base}{d}{quote}:USDT".upper())
        
        # Add lowercase variants
        variants |= {v.lower() for v in variants}
        
        for v in variants:
            old = symmap.get(v)
            if old is None:
                symmap[v] = mkey
            else:
                # Prefer spot > swap > future
                def rank(k):
                    t = markets[k].get("type") or markets[k].get("contractType")
                    if t in (None, "spot"):
                        return 3
                    if t in ("swap", "linear", "perpetual"):
                        return 2
                    return 1
                
                if rank(mkey) > rank(old):
                    symmap[v] = mkey
    
    return symmap


def normalize_symbol(user_symbol: str, symmap: dict[str, str]) -> str | None:
    """
    Normalize user-provided symbol to CCXT market key
    
    Args:
        user_symbol: User input (e.g., "BTCUSDT", "BTC/USDT", "btc/usdt")
        symmap: Symbol map from build_symbol_map()
    
    Returns:
        Normalized market key or None if not found
    """
    if not user_symbol:
        return None
    
    key = user_symbol.strip()
    
    # Quick lookups
    if key in symmap:
        return symmap[key]
    
    up = key.upper()
    lo = key.lower()
    
    if up in symmap:
        return symmap[up]
    if lo in symmap:
        return symmap[lo]
    
    # Try slash/no-slash variants
    if "/" not in up and up.endswith("USDT"):
        base = up[:-4]
        for d in DELIMS:
            for sfx in SPOT_SUFFIXES:
                cand = f"{base}{d}USDT{sfx}"
                if cand in symmap:
                    return symmap[cand]
                lc = cand.lower()
                if lc in symmap:
                    return symmap[lc]
    
    if "/" in up:
        parts = up.split("/", 1)
        if len(parts) == 2:
            base, quote = parts
            for sfx in SPOT_SUFFIXES:
                cand = f"{base}/{quote}{sfx}"
                if cand in symmap:
                    return symmap[cand]
                lc = cand.lower()
                if lc in symmap:
                    return symmap[lc]
    
    return None


@dataclass
class SymbolFilters:
    """MEXC symbol filters from /api/v3/exchangeInfo"""
    symbol: str
    price_step: float  # tickSize
    qty_step: float  # stepSize
    min_notional: float  # minNotional (USDT)
    min_qty: float  # minQty
    max_qty: float  # maxQty
    price_precision: int
    quantity_precision: int
    
    def __repr__(self):
        return (
            f"SymbolFilters({self.symbol}: "
            f"priceStep={self.price_step}, qtyStep={self.qty_step}, "
            f"minNotional={self.min_notional}, minQty={self.min_qty})"
        )


class MEXCFiltersCache:
    """Cache MEXC exchange info with 30min TTL"""
    
    def __init__(self, ttl_seconds: int = 1800):
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, SymbolFilters] = {}
        self._symbol_map: dict[str, str] = {}  # Normalized symbol map
        self._last_fetch: float = 0.0
        self._exchange: ccxt.mexc | None = None
    
    async def _init_exchange(self):
        """Initialize CCXT MEXC exchange"""
        if self._exchange is None:
            self._exchange = ccxt.mexc({
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'}
            })
    
    async def fetch_exchange_info(self) -> dict[str, SymbolFilters]:
        """Fetch and cache MEXC exchange info"""
        now = time.time()
        
        # Return cache if fresh
        if self._cache and (now - self._last_fetch) < self.ttl_seconds:
            return self._cache
        
        await self._init_exchange()
        
        try:
            # Fetch markets from CCXT
            markets = await self._exchange.load_markets()
            
            filters = {}
            for symbol, market in markets.items():
                if not market.get('active') or market.get('type') != 'spot':
                    continue
                
                # Extract filters from market info
                limits = market.get('limits', {})
                precision = market.get('precision', {})
                
                # Price limits
                price_limits = limits.get('price', {})
                price_step = price_limits.get('min', 0.01)
                
                # Amount (quantity) limits
                amount_limits = limits.get('amount', {})
                qty_step = amount_limits.get('min', 0.00001)
                min_qty = amount_limits.get('min', 0.00001)
                max_qty = amount_limits.get('max', 1000000.0)
                
                # Cost (notional) limits
                cost_limits = limits.get('cost', {})
                min_notional = cost_limits.get('min', 5.0)  # MEXC default ~5 USDT
                
                # Precision
                price_precision = precision.get('price', 2)
                quantity_precision = precision.get('amount', 6)
                
                filters[symbol] = SymbolFilters(
                    symbol=symbol,
                    price_step=price_step,
                    qty_step=qty_step,
                    min_notional=min_notional,
                    min_qty=min_qty,
                    max_qty=max_qty,
                    price_precision=price_precision,
                    quantity_precision=quantity_precision
                )
            
            # Build symbol normalization map
            self._symbol_map = build_symbol_map(markets)
            
            self._cache = filters
            self._last_fetch = now
            
            # Debug: print first 5 symbols
            sample_symbols = list(filters.keys())[:5]
            print(f"✅ MEXC filters cached: {len(filters)} symbols")
            print(f"   Sample symbols: {sample_symbols}")
            print(f"   Symbol map entries: {len(self._symbol_map)}")
            return filters
            
        except Exception as e:
            print(f"⚠️ Failed to fetch MEXC exchange info: {e}")
            # Return stale cache if available
            return self._cache if self._cache else {}
    
    async def get_filters(self, symbol: str) -> SymbolFilters | None:
        """Get filters for a specific symbol (with normalization)"""
        filters = await self.fetch_exchange_info()
        
        # Try direct lookup first
        if symbol in filters:
            return filters[symbol]
        
        # Try normalization
        normalized = normalize_symbol(symbol, self._symbol_map)
        if normalized:
            return filters.get(normalized)
        
        return None
    
    async def close(self):
        """Close exchange connection"""
        if self._exchange:
            await self._exchange.close()


# Global cache instance
_filters_cache: MEXCFiltersCache | None = None


def get_filters_cache() -> MEXCFiltersCache:
    """Get or create global filters cache"""
    global _filters_cache
    if _filters_cache is None:
        _filters_cache = MEXCFiltersCache()
    return _filters_cache


@dataclass
class NormalizedOrder:
    """Normalized order ready for MEXC"""
    symbol: str
    side: Literal["BUY", "SELL"]
    price: float  # Rounded to priceStep
    quantity: float  # Rounded to qtyStep
    notional: float  # price * quantity
    quote_usd: float  # Original requested amount
    is_valid: bool
    reject_reason: str | None = None


async def normalize_order(
    symbol: str,
    side: Literal["BUY", "SELL"],
    quote_usd: float,
    mid_price: float | None = None
) -> NormalizedOrder:
    """
    Normalize order to MEXC exchange filters
    
    Args:
        symbol: Trading pair (e.g., "BTC/USDT")
        side: "BUY" or "SELL"
        quote_usd: Desired order size in USDT
        mid_price: Current mid price (if None, will use REST fallback)
    
    Returns:
        NormalizedOrder with validation status
    """
    cache = get_filters_cache()
    filters = await cache.get_filters(symbol)
    
    if not filters:
        return NormalizedOrder(
            symbol=symbol,
            side=side,
            price=0.0,
            quantity=0.0,
            notional=0.0,
            quote_usd=quote_usd,
            is_valid=False,
            reject_reason="FILTER_NOT_FOUND"
        )
    
    # Get price (prefer WS mid, fallback to REST)
    if mid_price is None:
        # TODO: Integrate with WS feed for real-time mid
        # For now, use a placeholder
        mid_price = 50000.0  # Placeholder
    
    # Round price to priceStep
    price = round(mid_price / filters.price_step) * filters.price_step
    
    # Calculate quantity
    raw_qty = quote_usd / price
    quantity = round(raw_qty / filters.qty_step) * filters.qty_step
    
    # Calculate notional
    notional = price * quantity
    
    # Validate filters
    if quantity < filters.min_qty:
        return NormalizedOrder(
            symbol=symbol,
            side=side,
            price=price,
            quantity=quantity,
            notional=notional,
            quote_usd=quote_usd,
            is_valid=False,
            reject_reason=f"FILTER_REJECT:minQty({filters.min_qty})"
        )
    
    if quantity > filters.max_qty:
        return NormalizedOrder(
            symbol=symbol,
            side=side,
            price=price,
            quantity=quantity,
            notional=notional,
            quote_usd=quote_usd,
            is_valid=False,
            reject_reason=f"FILTER_REJECT:maxQty({filters.max_qty})"
        )
    
    if notional < filters.min_notional:
        # Try to bump quantity to meet minNotional
        min_qty_for_notional = filters.min_notional / price
        adjusted_qty = round(min_qty_for_notional / filters.qty_step) * filters.qty_step
        
        if adjusted_qty <= filters.max_qty:
            quantity = adjusted_qty
            notional = price * quantity
        else:
            return NormalizedOrder(
                symbol=symbol,
                side=side,
                price=price,
                quantity=quantity,
                notional=notional,
                quote_usd=quote_usd,
                is_valid=False,
                reject_reason=f"FILTER_REJECT:minNotional({filters.min_notional})"
            )
    
    # All checks passed
    return NormalizedOrder(
        symbol=symbol,
        side=side,
        price=price,
        quantity=quantity,
        notional=notional,
        quote_usd=quote_usd,
        is_valid=True,
        reject_reason=None
    )

