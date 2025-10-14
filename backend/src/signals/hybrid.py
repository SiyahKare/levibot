from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from ..app import config as app_cfg
from ..features.telegram_bias import compute_telegram_bias_with_age
from ..features.telegram_pulse import compute_pulse_factor
from .baseline import BaselineSignal, compute_baseline
from .ml_model import ml_score
from .trend import trend_score


@dataclass
class HybridSignal:
    side: str  # long/short/flat
    score: float
    components: dict


def eth_led_altseason_trigger(meta: dict) -> bool:
    """
    Placeholder: return True if ETH/BTC trend up and BTC.D down, TOTAL3 up.
    Expect meta dict with keys: ethbtc_trend, btc_dom_trend, total3_trend.
    """
    return (
        meta.get("ethbtc_trend", 0.0) > 0
        and meta.get("btc_dom_trend", 0.0) < 0
        and meta.get("total3_trend", 0.0) > 0
    )


def combine_signals(
    df: pl.DataFrame,
    ml_proba: float | None,
    news_bias: float,
    meta: dict | None = None,
) -> HybridSignal:
    # Gerçek skorlar: sembolden oku (fallback baseline)
    symbol = df.select(pl.first("symbol")).item() if "symbol" in df.columns else None
    if symbol:
        t = trend_score(symbol, timeframe="1m")
        m = ml_score(symbol, timeframe="1m")
        ml_component = (m or 0.5) - 0.5
        side_bias = 1.0 if t >= 0.5 else -1.0 if t < 0.5 else 0.0
        base_strength = abs(t - 0.5) * 2.0
        base_score = side_bias * base_strength
    else:
        base: BaselineSignal = compute_baseline(df)
        ml_component = (ml_proba or 0.5) - 0.5
        side_bias = (
            1.0 if base.side == "long" else -1.0 if base.side == "short" else 0.0
        )
        base_score = side_bias * base.strength
    side_bias = 1.0 if base.side == "long" else -1.0 if base.side == "short" else 0.0
    base_score = side_bias * base.strength
    # Telegram bias: sembol df içinde var, config'ten yarı ömür ve min reputation çek
    symbol = symbol or (
        df.select(pl.first("symbol")).item() if "symbol" in df.columns else None
    )
    tel_bias = 0.0
    latest_age_min = None
    if symbol:
        try:
            half_life_min = (
                app_cfg.load_features_config()
                .get("telegram", {})
                .get("evaluation", {})
                .get("half_life_min", 120)
            )
            min_rep = (
                app_cfg.load_features_config()
                .get("telegram", {})
                .get("evaluation", {})
                .get("min_reputation", 0.35)
            )
            pulse_cfg = (
                app_cfg.load_features_config()
                .get("telegram", {})
                .get("evaluation", {})
                .get("pulse", {})
            )
        except Exception:
            half_life_min, min_rep = 120, 0.35
            pulse_cfg = {}
        tel_bias, latest_age_min = compute_telegram_bias_with_age(
            symbol, half_life_min=half_life_min, min_rep=min_rep
        )
        # gate cfg
        gate_cfg = (
            app_cfg.load_features_config()
            .get("telegram", {})
            .get("evaluation", {})
            .get("gate", {})
        )
        min_abs = float(gate_cfg.get("min_abs_bias", 0.02))
        max_age = int(gate_cfg.get("max_age_min", half_life_min))
        gate_reason = None
        if latest_age_min is None:
            gate_reason = "no_signal"
            tel_bias = 0.0
        elif latest_age_min > max_age:
            gate_reason = "stale"
            tel_bias = 0.0
        elif abs(tel_bias) < min_abs:
            gate_reason = "bias_too_small"
            tel_bias = 0.0
        total = base_score + ml_component + news_bias + tel_bias
    else:
        total = base_score + ml_component + news_bias
    side = "long" if total > 0.05 else "short" if total < -0.05 else "flat"

    if meta and not eth_led_altseason_trigger(meta):
        # Only allow alts when ETH-led trigger fires; otherwise neutralize non-ETH signals.
        total *= 0.5
        side = "flat" if abs(total) < 0.1 else side

    # Pulse sizing hesapla (symbol varsa)
    pulse_factor = 1.0
    pulse_meta = None
    if symbol:
        pulse_factor, pulse_age, pulse_side = compute_pulse_factor(
            symbol,
            target_mult=float(pulse_cfg.get("size_multiplier", 1.2)),
            decay_min=int(pulse_cfg.get("decay_min", 30)),
            window_min=int(pulse_cfg.get("window_min", 15)),
            min_count=int(pulse_cfg.get("min_count", 3)),
            min_rep=float(pulse_cfg.get("min_rep", 0.5)),
        )
        pulse_factor = min(pulse_factor, float(pulse_cfg.get("hard_cap", 1.5)))
        pulse_meta = {"factor": pulse_factor, "side": pulse_side, "age_min": pulse_age}

    return HybridSignal(
        side=side,
        score=float(total),
        components={
            "baseline": base_score,
            "ml": ml_component,
            "news": news_bias,
            "telegram_bias": tel_bias,
            "telegram_pulse": pulse_meta,
        },
    )
