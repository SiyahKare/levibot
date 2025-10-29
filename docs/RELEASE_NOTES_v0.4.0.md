# LeviBot v0.4.0 (miniface)

## Yeni

- apps/executor/schemas.py – Pydantic istek/yanıt modelleri
- apps/executor/routes.py – /signals/run, /exec/dry-run, /exec/submit
- apps/executor/risk.py – evaluate_and_filter + JSONL veto log
- apps/executor/adapters.py – legacy alias + deprecate header (EOL: 2025-11-30)
- apps/executor/main.py – /healthz, /metrics, factory
- apps/executor/chain.py – Base Sepolia adapter (env yoksa 0xMOCK)
- pkgs/core, pkgs/signals, pkgs/backtest – paket ayrıştırma (STRATEGIES, ta.py, compute_metrics)
- CI – minimal: pytest smoke + web3/prometheus-client deps

## Kırıcı Değişiklikler

- Public API 3 endpoint ile sabitlendi; legacy rotalar kaldırılacak (tarih üstte).

## Bilinen Kısıtlar

- /exec/submit MVP: tek hedef adrese calldata; Safe Module/4337 “session key” sonraki sürüm.
