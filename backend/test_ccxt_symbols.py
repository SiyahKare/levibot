import asyncio

import ccxt.async_support as ccxt


async def test():
    ex = ccxt.mexc()
    await ex.load_markets()
    symbols = list(ex.markets.keys())
    print(f"Total markets: {len(symbols)}")
    print(f"First 10: {symbols[:10]}")
    
    # Check BTC
    btc_markets = [s for s in symbols if 'BTC' in s and 'USDT' in s][:5]
    print(f"BTC/USDT markets: {btc_markets}")
    
    await ex.close()

asyncio.run(test())

