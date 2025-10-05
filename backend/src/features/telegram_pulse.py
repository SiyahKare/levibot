import datetime as dt
import duckdb as d


def last_burst(symbol: str, *, window_min: int = 15, min_count: int = 3, min_rep: float = 0.5):
    now = dt.datetime.utcnow()
    since = (now - dt.timedelta(minutes=window_min)).strftime("%Y-%m-%dT%H:%M:%SZ")
    df = d.sql(
        """
        WITH sx AS (
          SELECT ts,
                 payload->'signal'->>'symbol' AS symbol,
                 UPPER(payload->'signal'->>'side') AS side,
                 payload->>'chat_title' AS chat
          FROM read_json_auto('backend/data/logs/*/events-*.jsonl')
          WHERE event_type='SIGNAL_EXT_TELEGRAM' AND ts >= ? AND payload->'signal'->>'symbol' = ?
        ),
        rep AS (
          SELECT chat, reputation FROM read_parquet('backend/data/derived/telegram_reputation.parquet')
        )
        SELECT sx.symbol, sx.side,
               COUNT(*) AS n,
               AVG(COALESCE(rep.reputation,0)) AS avg_rep,
               MAX(sx.ts) AS latest_ts
        FROM sx LEFT JOIN rep ON rep.chat = sx.chat
        GROUP BY sx.symbol, sx.side
        HAVING n >= ?
        """,
        [since, symbol, min_count],
    ).df()
    if df.empty:
        return None
    df = df.sort_values(["n", "latest_ts"], ascending=[False, False])
    row = df.iloc[0]
    if float(row.avg_rep) < float(min_rep):
        return None
    return {
        "side": str(row.side),
        "count": int(row.n),
        "avg_rep": float(row.avg_rep),
        "latest_ts": str(row.latest_ts),
    }


def compute_pulse_factor(
    symbol: str,
    *,
    target_mult: float = 1.20,
    decay_min: int = 30,
    window_min: int = 15,
    min_count: int = 3,
    min_rep: float = 0.5,
):
    b = last_burst(symbol, window_min=window_min, min_count=min_count, min_rep=min_rep)
    if not b:
        return 1.0, None, None
    now = dt.datetime.utcnow()
    latest = dt.datetime.fromisoformat(b["latest_ts"].replace("Z", "+00:00"))
    age_min = max(0.0, (now - latest).total_seconds() / 60.0)
    if age_min >= decay_min:
        return 1.0, age_min, b["side"]
    pulse = 1.0 + (target_mult - 1.0) * (0.5 ** (age_min / float(decay_min)))
    return max(1.0, pulse), age_min, b["side"]
















