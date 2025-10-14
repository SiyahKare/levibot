from __future__ import annotations

from fastapi import APIRouter

from ..reports.telegram_eval import eval_signals, save_eval_parquet
from ..reports.telegram_reputation import compute_reputation, save_reputation_parquet

router = APIRouter()


@router.post("/admin/recompute-telegram")
def recompute_telegram():
    rows = eval_signals("backend/data/logs/*/events-*.jsonl")
    p1 = save_eval_parquet(rows)
    rep = compute_reputation("backend/data/logs/*/events-*.jsonl", days=14)
    p2 = save_reputation_parquet(rep)
    return {
        "ok": True,
        "eval_path": p1,
        "rep_path": p2,
        "eval_rows": len(rows or []),
        "groups": len(rep or []),
    }
