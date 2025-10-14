from __future__ import annotations

import datetime as dt
import hashlib

import duckdb as d
from apscheduler.schedulers.background import BackgroundScheduler

from ..alerts.notify import send as tg_send
from ..infra.logger import log_event
from ..mev.arb_scan import scan_once
from ..mev.snapshot import write_snapshots
from ..reports.telegram_eval import eval_signals, save_eval_parquet
from ..reports.telegram_reputation import compute_reputation, save_reputation_parquet


def schedule_jobs() -> BackgroundScheduler:
    sched = BackgroundScheduler(timezone="UTC")

    @sched.scheduled_job("cron", minute="*/15")
    def refresh_telegram_reputation():
        try:
            rows = eval_signals("backend/data/logs/*/events-*.jsonl")
            save_eval_parquet(rows)
            rep = compute_reputation("backend/data/logs/*/events-*.jsonl", days=14)
            save_reputation_parquet(rep)
            log_event(
                "TELEGRAM_REP_REFRESH",
                {"eval_rows": len(rows or []), "groups": len(rep or [])},
            )
        except Exception as e:
            log_event("ERROR", {"scope": "telegram_rep_job", "err": str(e)})

    @sched.scheduled_job("cron", second="20", minute="*")
    def mev_snap_and_scan():
        try:
            write_snapshots()
            scan_once(["ETHUSDT", "BTCUSDT", "SOLUSDT"])
        except Exception as e:
            log_event("ERROR", {"scope": "mev_snap_and_scan", "err": str(e)})

    sched.start()
    return sched


# Basit proses-içi dedupe set'i (uygulama ömrü boyunca)
SEEN_ALERTS = set()


def _register_burst_job(sched: BackgroundScheduler) -> None:
    @sched.scheduled_job("cron", minute="*")
    def telegram_burst_alert():
        now = dt.datetime.utcnow()
        since = (now - dt.timedelta(minutes=15)).strftime("%Y-%m-%dT%H:%M:%SZ")
        df = d.sql(
            """
            WITH sx AS (
              SELECT ts,
                     payload->'signal'->>'symbol' AS symbol,
                     UPPER(payload->'signal'->>'side') AS side,
                     payload->>'chat_title' AS chat
              FROM read_json_auto('backend/data/logs/*/events-*.jsonl')
              WHERE event_type='SIGNAL_EXT_TELEGRAM' AND ts >= ?
            ),
            rep AS (
              SELECT chat, reputation FROM read_parquet('backend/data/derived/telegram_reputation.parquet')
            )

    @sched.scheduled_job("cron", second="5", minute="*")
    def run_perp_breakout():
        try:
            pb_tick(user_id="default")
        except Exception as e:
            log_event("ERROR", {"scope": "pb_tick", "err": str(e)})

    @sched.scheduled_job("cron", second="10", minute="*")
    def run_twap_bot():
        try:
            twap_tick(user_id="default")
        except Exception as e:
            log_event("ERROR", {"scope": "twap_tick", "err": str(e)})
            SELECT sx.symbol, sx.side,
                   COUNT(*) AS n,
                   AVG(COALESCE(rep.reputation,0)) AS avg_rep,
                   MAX(sx.ts) AS latest_ts
            FROM sx LEFT JOIN rep ON rep.chat = sx.chat
            GROUP BY sx.symbol, sx.side
            HAVING n >= 3
            """,
            [since],
        ).df()
        for _, r in df.iterrows():
            try:
                latest_age_min = (
                    now
                    - dt.datetime.fromisoformat(str(r.latest_ts).replace("Z", "+00:00"))
                ).total_seconds() / 60.0
            except Exception:
                continue
            if latest_age_min > 30:
                continue
            if float(r.avg_rep) < 0.5:
                continue
            key = f"{r.symbol}:{r.side}:{since[:16]}"
            h = hashlib.sha1(key.encode()).hexdigest()
            if h in SEEN_ALERTS:
                continue
            SEEN_ALERTS.add(h)
            log_event(
                "ALERT_TELEGRAM_BURST",
                {
                    "symbol": r.symbol,
                    "side": r.side,
                    "count": int(r.n),
                    "avg_reputation": float(r.avg_rep),
                    "latest_age_min": latest_age_min,
                },
            )
            tg_send(
                f"🚨 Telegram Burst\n"
                f"• {r.symbol} {r.side}\n"
                f"• Signals: {int(r.n)}  • Avg rep: {float(r.avg_rep):.2f}\n"
                f"• Latest age: {latest_age_min:.0f} min"
            )
