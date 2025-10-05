#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../"
python3 -m venv .venv || true
source .venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r backend/requirements.txt
python3 - <<'PY'
from backend.src.ml.retrain import main
main()
PY



