#!/usr/bin/env bash
set -euo pipefail

echo "[1/6] Start API (terminal 1): make api_miniface"
echo "Open http://localhost:8000/docs"

echo "[2/6] Run signals (sma 10/50)"
curl -sX POST localhost:8000/signals/run -H 'content-type: application/json' \
 -d '{"strategy":"sma","params":{"fast":10,"slow":50},"fee_bps":10}' | tee /tmp/run.json | jq .

echo "[3/6] Dry-run with slippage=25bps"
jq '{orders: .orders, slippage_bps: 25}' /tmp/run.json \
 | curl -sX POST localhost:8000/exec/dry-run -H 'content-type: application/json' -d @- | jq .

echo "[4/6] Submit (base-sepolia if env set)"
jq '{orders: .orders, network: "base-sepolia"}' /tmp/run.json \
 | curl -sX POST localhost:8000/exec/submit -H 'content-type: application/json' -d @- | tee /tmp/tx.json | jq .

echo "[5/6] Telemetry head"
curl -s localhost:8000/metrics | head -n 20

echo "[6/6] Done."


