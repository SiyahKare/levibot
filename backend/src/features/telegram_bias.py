from __future__ import annotations

import datetime as dt
import duckdb as d


def last_signals(symbol: str, minutes: int = 120, now: dt.datetime | None = None):
    now = now or dt.datetime.utcnow()
    since = (now - dt.timedelta(minutes=minutes)).strftime("%Y-%m-%dT%H:%M:%SZ")
    sql = """
    SELECT ts, payload->>'chat_title' AS chat,
           payload->'signal'->>'side' AS side,
           TRY_CAST(payload->'signal'->>'confidence' AS DOUBLE) AS conf
    FROM read_json_auto('backend/data/logs/*/events-*.jsonl')
    WHERE event_type='SIGNAL_EXT_TELEGRAM'
      AND payload->'signal'->>'symbol' = ?
      AND ts >= ?
    ORDER BY ts DESC
    """
    return d.sql(sql, [symbol, since]).df()


def load_reputation(parquet_path: str = "backend/data/derived/telegram_reputation.parquet") -> dict:
    try:
        df = d.sql(f"SELECT * FROM read_parquet('{parquet_path}')").df()
        return {r.chat: r.reputation for _, r in df.iterrows()}
    except Exception:
        return {}


def compute_telegram_bias_with_age(symbol: str, *, half_life_min: int = 120, min_rep: float = 0.35) -> tuple[float, float | None]:
    """Bias ile birlikte en taze sinyal yaşını (dakika) döndürür."""
    now = dt.datetime.utcnow()
    df = last_signals(symbol, minutes=half_life_min * 3, now=now)
    reps = load_reputation()
    if df.empty:
        return 0.0, None
    # En taze kayıt yaşı
    latest_ts = dt.datetime.fromisoformat(str(df.iloc[0].ts).replace("Z", "+00:00"))
    latest_age_min = max(0.0, (now - latest_ts).total_seconds() / 60.0)
    # Bias birikimi
    acc = 0.0
    for _, r in df.iterrows():
        rep = float(reps.get(r.chat, 0.0))
        if rep < min_rep:
            continue
        sgn = +1.0 if str(r.side).upper() in ("LONG", "BUY") else -1.0
        age_min = max(0.0, (now - dt.datetime.fromisoformat(str(r.ts).replace("Z", "+00:00"))).total_seconds() / 60.0)
        decay = 0.5 ** (age_min / float(half_life_min))
        acc += sgn * float((r.conf if r.conf is not None else 0.6)) * rep * decay
    bias = max(-0.15, min(0.15, acc * 0.15))
    return bias, latest_age_min


