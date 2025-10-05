import os
import argparse
import duckdb as d
import pandas as pd
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score


def load_ohlcv(symbol: str, timeframe: str):
    path = f"backend/data/parquet/ohlcv/{symbol}_{timeframe}.parquet"
    return d.sql(f"SELECT time, open, high, low, close FROM read_parquet('{path}') ORDER BY time").df()


def make_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["ret1"] = df["close"].pct_change()
    df["vol"] = (df["high"] - df["low"]) / df["close"]
    df["ma21"] = df["close"].rolling(21).mean() / df["close"] - 1
    df["ma55"] = df["close"].rolling(55).mean() / df["close"] - 1
    df = df.dropna()
    return df


def make_labels(df: pd.DataFrame, horizon: int = 30, thr: float = 0.001):
    fut = df["close"].shift(-horizon)
    retH = (fut / df["close"] - 1.0)
    y = (retH > thr).astype(int)
    df = df.iloc[:-horizon].copy()
    y = y.iloc[:-horizon]
    return df, y


def train(symbols, timeframe="1m", horizon=30, thr=0.001, out="backend/models/linlogit.joblib"):
    Xs, ys = [], []
    for sym in symbols:
        df = load_ohlcv(sym, timeframe)
        if df.empty:
            continue
        df = make_features(df)
        df, y = make_labels(df, horizon=horizon, thr=thr)
        X = df[["ret1", "vol", "ma21", "ma55"]]
        if len(X) < 200:
            continue
        Xs.append(X.values)
        ys.append(y.values)
    if not Xs:
        raise SystemExit("No data to train")
    X = np.vstack(Xs)
    y = np.concatenate(ys)
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, shuffle=False)
    clf = LogisticRegression(max_iter=200)
    clf.fit(Xtr, ytr)
    auc = roc_auc_score(yte, clf.predict_proba(Xte)[:, 1])
    os.makedirs(os.path.dirname(out), exist_ok=True)
    joblib.dump(clf, out)
    print(f"Saved {out}, test AUC={auc:.3f}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--symbols", nargs="+", default=["ETHUSDT", "BTCUSDT", "SOLUSDT"])
    p.add_argument("--timeframe", default="1m")
    p.add_argument("--horizon", type=int, default=30)
    p.add_argument("--thr", type=float, default=0.001)
    p.add_argument("--out", default="backend/models/linlogit.joblib")
    a = p.parse_args()
    train(a.symbols, a.timeframe, a.horizon, a.thr, a.out)
















