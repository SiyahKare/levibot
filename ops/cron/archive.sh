#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."

# venv opsiyonel; prod docker'da gerekmez
if [ -d ".venv" ]; then source .venv/bin/activate; fi

export PYTHONUNBUFFERED=1
echo "[cron] S3 archiver running at $(date -u +%F\ %T)Z"
python -m backend.src.ops.s3_archiver
