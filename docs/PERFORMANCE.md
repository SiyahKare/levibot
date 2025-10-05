# Performance Baseline

Bu doküman LeviBot API için temel **benchmark** akışını ve karşılaştırma yöntemini açıklar.  
Araç: [`pytest-benchmark`](https://pytest-benchmark.readthedocs.io/)

## Hızlı Başlangıç

```bash
# Kurulum (gerekirse)
source .venv/bin/activate
pip install pytest-benchmark

# Sadece benchmark'lar
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
pytest backend/tests/test_performance.py --benchmark-only -q

# Baseline kaydet (örn. v1.3)
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
pytest backend/tests/test_performance.py --benchmark-only --benchmark-save=baseline-v1.3 -q
```

## Karşılaştırma (Regression Tespiti)

```bash
# Yeni değişiklik sonrası ölç ve compare
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
pytest backend/tests/test_performance.py --benchmark-only \
  --benchmark-compare=baseline-v1.3 -q
```

> **Öneri:** CI'da PR başına `--benchmark-compare` çalıştırıp,
> % fark belli eşiği aşarsa uyarı verin.

## Metodoloji

* **Senaryolar**
  * `/readyz`  → servis canlılık
  * `/signals/score` → ML scoring (TF-IDF + Calibrated SVC)
  * `/dex/quote` → DEX quote (offline fallback'lı)
* **Ölçümler**
  * `pytest-benchmark`: ort/medyan/p90/p99
  * Hızlı koruma: `PERF_P99_BUDGET_MS` (varsayılan 120 ms) ile basit sınır

## İpuçları

* Lokal dalgalanmayı azaltmak için:
  * Diğer yoğun süreçleri kapatın
  * Sanal makine/CI'da sabit donanım profili kullanın
* Prod gözlemi için Prometheus:
  * `levibot_http_request_latency_seconds` histogramını Grafana'da p95/p99 izleyin
