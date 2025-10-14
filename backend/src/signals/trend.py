import duckdb as d
import numpy as np


def trend_score(
    symbol: str,
    timeframe: str = "1m",
    fast: int = 21,
    slow: int = 55,
    adx_len: int = 14,
) -> float:
    path = f"backend/data/parquet/ohlcv/{symbol}_{timeframe}.parquet"
    df = d.sql(
        f"SELECT close, high, low FROM read_parquet('{path}') ORDER BY time"
    ).df()
    if df.empty:
        return 0.5
    c = df["close"].to_numpy(float)

    def ema(x: np.ndarray, n: int) -> np.ndarray:
        a = 2 / (n + 1)
        y = np.zeros_like(x)
        y[0] = x[0]
        for i in range(1, len(x)):
            y[i] = a * x[i] + (1 - a) * y[i - 1]
        return y

    efast, eslow = ema(c, fast), ema(c, slow)
    cross = 1.0 if efast[-1] > eslow[-1] else 0.0
    h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float)
    tr = np.maximum(
        h - l, np.maximum(np.abs(h - np.roll(c, 1)), np.abs(l - np.roll(c, 1)))
    )
    tr[0] = h[0] - l[0]
    up = np.clip(h - np.roll(h, 1), 0, None)
    dn = np.clip(np.roll(l, 1) - l, 0, None)
    up[0] = 0
    dn[0] = 0
    pdi = (
        100 * np.convolve(up, np.ones(adx_len) / adx_len, "same") / np.maximum(tr, 1e-9)
    )
    ndi = (
        100 * np.convolve(dn, np.ones(adx_len) / adx_len, "same") / np.maximum(tr, 1e-9)
    )
    dx = 100 * np.abs(pdi - ndi) / np.maximum(pdi + ndi, 1e-9)
    adx = float(np.mean(dx[-adx_len:]))
    qual = min(adx / 30.0, 1.0)
    return float(0.5 + (cross - 0.5) * qual)
