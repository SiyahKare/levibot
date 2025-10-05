from __future__ import annotations

from typing import List, Dict, Any
import duckdb as d
import pandas as pd
from pathlib import Path


def compute_reputation(day_glob: str, eval_parquet: str = "backend/data/derived/telegram_eval.parquet", days: int = 14) -> List[Dict[str, Any]]:
    try:
        df = d.sql(
            f"""
            SELECT chat,
                   AVG(CASE WHEN outcome='TP' THEN 1 WHEN outcome='SL' THEN 0 ELSE 0.5 END) AS hit,
                   AVG(rr) AS avg_rr,
                   median(mfe) AS med_mfe,
                   median(abs(mae)) AS med_mae,
                   COUNT(*) AS n
            FROM read_parquet('{eval_parquet}')
            GROUP BY chat
            ORDER BY n DESC
            """
        ).df()
    except Exception:
        return []
    rep: List[Dict[str, Any]] = []
    for _, r in df.iterrows():
        med_mae = float(r.med_mae) if r.med_mae is not None else 1.0
        mfe_mae = float(r.med_mfe) / (med_mae + 1e-9)
        score = 0.5 * float(r.hit) + 0.3 * max(min(float(r.avg_rr) / 1.5, 1.0), 0.0) + 0.2 * max(min(mfe_mae / 1.2, 1.0), 0.0)
        score = max(0.0, min(1.0, score))
        rep.append({"chat": r.chat, "reputation": score, "signals": int(r.n)})
    return rep


def save_reputation_parquet(rows: List[Dict[str, Any]], out_path: str = "backend/data/derived/telegram_reputation.parquet") -> str:
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        # boş dosya yazmak yerine path'i döndür
        return str(p)
    pd.DataFrame(rows).to_parquet(p)
    return str(p)
