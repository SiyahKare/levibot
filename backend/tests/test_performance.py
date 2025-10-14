from __future__ import annotations

import json
import os

from fastapi.testclient import TestClient

from backend.src.app.main import app

# Not: Bu testler "benchmark" fixture'ını kullanır (pytest-benchmark)
# Çalıştırma:
#   PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q backend/tests/test_performance.py --benchmark-only
# Kayıt:
#   ... --benchmark-save=baseline-v1.3

client = TestClient(app)


def _score_once():
    r = client.post("/signals/score?text=BUY%20BTCUSDT%20@%2060000")
    return r.status_code


def _dex_quote_once():
    r = client.get("/dex/quote?sell=ETH&buy=USDC&amount=0.1")
    return r.status_code


def _readyz_once():
    r = client.get("/readyz")
    return r.status_code


def test_readyz_bench(benchmark):
    code = benchmark(_readyz_once)
    assert code == 200


def test_score_bench(benchmark):
    code = benchmark(_score_once)
    assert code == 200


def test_dex_quote_bench(benchmark):
    code = benchmark(_dex_quote_once)
    assert code == 200


def test_score_p99_budget():
    """
    Hızlı koruma: lokal/CI koşullarında p99 için basit sınır.
    Çevresel değişkenle ayarlanabilir.
    """
    import time

    budget_ms = float(os.getenv("PERF_P99_BUDGET_MS", "120.0"))
    samples = []
    for _ in range(30):
        t0 = time.perf_counter()
        assert _score_once() == 200
        dt = (time.perf_counter() - t0) * 1000.0
        samples.append(dt)
    samples.sort()
    p99 = samples[int(len(samples) * 0.99) - 1]
    # p99 değeri JSON ekstra çıktı olarak sakla (CI artefact'ı için kullanışlı)
    print(json.dumps({"metric": "score_p99_ms", "value": p99}))
    assert p99 <= budget_ms
