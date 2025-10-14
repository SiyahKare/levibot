import os

import duckdb as d

try:
    import joblib  # type: ignore
except Exception:
    joblib = None

MODEL_PATH = os.getenv("ML_MODEL_PATH", "backend/models/linlogit_cal.joblib")
_model = None


def _load():
    global _model
    if _model is None and joblib is not None:
        try:
            _model = joblib.load(MODEL_PATH)
        except Exception:
            _model = None
    return _model


def features_df(symbol: str, timeframe: str = "1m", lookback: int = 100):
    path = f"backend/data/parquet/ohlcv/{symbol}_{timeframe}.parquet"
    df = d.sql(
        f"SELECT time, open, high, low, close FROM read_parquet('{path}') ORDER BY time DESC LIMIT {lookback}"
    ).df()
    if df.empty:
        return None
    df = df.iloc[::-1].reset_index(drop=True)
    df["ret1"] = df["close"].pct_change()
    df["vol"] = (df["high"] - df["low"]) / df["close"]
    df["ma21"] = df["close"].rolling(21).mean() / df["close"] - 1
    df["ma55"] = df["close"].rolling(55).mean() / df["close"] - 1
    df = df.dropna()
    return df[["ret1", "vol", "ma21", "ma55"]].iloc[[-1]]


def ml_score(symbol: str, timeframe: str = "1m") -> float:
    X = features_df(symbol, timeframe)
    if X is None or X.empty:
        return 0.5
    m = _load()
    if m is None:
        return 0.5
    try:
        cal = m.get("cal") if isinstance(m, dict) else None
        base = m.get("base") if isinstance(m, dict) else m
        if cal is not None:
            p = float(cal.predict_proba(X.values)[0, 1])
        elif base is not None:
            p = float(base.predict_proba(X.values)[0, 1])
        else:
            p = 0.5
    except Exception:
        return 0.5
    return max(0.0, min(1.0, p))
