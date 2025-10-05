import os, argparse, json
import duckdb as d
import pandas as pd
import numpy as np
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import roc_auc_score, brier_score_loss


def load_ohlcv(symbol, tf):
    p = f"backend/data/parquet/ohlcv/{symbol}_{tf}.parquet"
    return d.sql(f"SELECT time, open, high, low, close FROM read_parquet('{p}') ORDER BY time").df()


def make_features(df: pd.DataFrame):
    df = df.copy()
    df["ret1"] = df["close"].pct_change()
    df["vol"] = (df["high"] - df["low"]) / df["close"]
    df["ma21"] = df["close"].rolling(21).mean() / df["close"] - 1
    df["ma55"] = df["close"].rolling(55).mean() / df["close"] - 1
    df = df.dropna()
    return df


def make_labels(df: pd.DataFrame, horizon=30, thr=0.001):
    fut = df["close"].shift(-horizon)
    retH = (fut / df["close"] - 1.0)
    y = (retH > thr).astype(int)
    df = df.iloc[:-horizon].copy()
    y = y.iloc[:-horizon]
    X = df[["ret1", "vol", "ma21", "ma55"]].values
    t = pd.to_datetime(df["time"]).astype(np.int64) // 10 ** 9
    return X, y.values, t.values


def time_folds(timestamps, n_folds=5):
    n = len(timestamps)
    fold_size = n // (n_folds + 1)
    for k in range(1, n_folds + 1):
        split = fold_size * k
        tr_idx = np.arange(0, split)
        va_idx = np.arange(split, min(split + fold_size, n))
        if len(va_idx) == 0:
            break
        yield tr_idx, va_idx


def train(symbols, timeframe, horizon, thr, n_folds, out_model, out_report):
    Xs, ys, ts = [], [], []
    for s in symbols:
        df = load_ohlcv(s, timeframe)
        if df.empty:
            continue
        df = make_features(df)
        X, y, t = make_labels(df, horizon, thr)
        if len(y) < 500:
            continue
        Xs.append(X)
        ys.append(y)
        ts.append(t)
    if not Xs:
        raise SystemExit("No data")
    X = np.vstack(Xs)
    y = np.concatenate(ys)
    t = np.concatenate(ts)
    order = np.argsort(t)
    X, y, t = X[order], y[order], t[order]
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    metrics = []
    clf_final = None
    cal_final = None
    for i, (tr, va) in enumerate(time_folds(t, n_folds), start=1):
        Xtr, ytr = X[tr], y[tr]
        Xva, yva = X[va], y[va]
        base = LogisticRegression(max_iter=300)
        base.fit(Xtr, ytr)
        cal = CalibratedClassifierCV(base_estimator=base, method="isotonic", cv="prefit")
        cal.fit(Xva, yva)
        p = cal.predict_proba(Xva)[:, 1]
        auc = roc_auc_score(yva, p)
        brier = brier_score_loss(yva, p)
        metrics.append({"fold": i, "auc": float(auc), "brier": float(brier), "n_val": int(len(yva))})
        clf_final, cal_final = base, cal

    os.makedirs(os.path.dirname(out_model), exist_ok=True)
    joblib.dump({"base": clf_final, "cal": cal_final}, out_model)
    with open(out_report, "w") as f:
        json.dump({"metrics": metrics}, f, indent=2)
    print(f"Saved {out_model}; metrics: {metrics}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", nargs="+", default=["ETHUSDT", "BTCUSDT", "SOLUSDT"])
    ap.add_argument("--timeframe", default="1m")
    ap.add_argument("--horizon", type=int, default=30)
    ap.add_argument("--thr", type=float, default=0.001)
    ap.add_argument("--folds", type=int, default=5)
    ap.add_argument("--out_model", default="backend/models/linlogit_cal.joblib")
    ap.add_argument("--out_report", default="backend/models/linlogit_cal_report.json")
    a = ap.parse_args()
    train(a.symbols, a.timeframe, a.horizon, a.thr, a.folds, a.out_model, a.out_report)
















