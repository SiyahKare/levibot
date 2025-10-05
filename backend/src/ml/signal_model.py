from __future__ import annotations
import os
import json
import joblib
import re
from pathlib import Path
from typing import List, Tuple

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report

MODEL_DIR = Path(os.getenv("MODEL_DIR", "backend/artifacts"))
DATA_PATH = Path("backend/data/signals/labels.jsonl")
MODEL_PATH = MODEL_DIR / "signal_clf.joblib"

LABELS = ["BUY", "SELL", "NO-TRADE"]


def _normalize(text: str) -> str:
    t = text.strip().lower()
    t = re.sub(r"[@#]", " ", t)
    t = re.sub(r"[^a-z0-9/.\-_\s]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t


def load_dataset(path=DATA_PATH) -> Tuple[List[str], List[str]]:
    X, y = [], []
    if not path.exists():
        return X, y
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            try:
                obj = json.loads(line)
                X.append(_normalize(obj["text"]))
                y.append(obj["label"].upper())
            except Exception:
                continue
    return X, y


def train_and_save():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    X, y = load_dataset()
    if not X:
        raise RuntimeError("no training data at backend/data/signals/labels.jsonl")
    
    # Base pipeline: TF-IDF + LinearSVC
    base_pipe = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_features=20000)),
            ("clf", LinearSVC()),
        ]
    )
    
    # Wrap with CalibratedClassifierCV for proper probabilities
    calibrated = CalibratedClassifierCV(base_pipe, method="sigmoid", cv=3 if len(X) >= 10 else 2)
    calibrated.fit(X, y)
    
    joblib.dump(calibrated, MODEL_PATH)
    pred = calibrated.predict(X)
    print(classification_report(y, pred, labels=LABELS))
    return MODEL_PATH


def load_model():
    if MODEL_PATH.exists():
        return joblib.load(MODEL_PATH)
    # cold start: train on the fly if dataset present
    return joblib.load(train_and_save())


def infer(text: str) -> Tuple[str, float]:
    """Predict label and calibrated confidence (0-1) for single text."""
    model = load_model()
    p = _normalize(text)
    label = model.predict([p])[0]
    
    try:
        # Use predict_proba for calibrated confidence
        proba = model.predict_proba([p])[0]
        conf = float(max(proba))  # max class probability
    except Exception:
        # Fallback if model doesn't support predict_proba
        conf = 0.5
    
    return label, conf

