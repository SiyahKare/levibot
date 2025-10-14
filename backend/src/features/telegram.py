from __future__ import annotations


def telegram_bias(
    model_direction: str | None,
    signal_direction: str | None,
    group_reputation: float = 1.0,
    max_bias: float = 0.15,
) -> float:
    """
    Basit bias fonksiyonu: yön uyumuna göre +/- bias verir ve grup itibarını uygular.
    model_direction: "LONG" | "SHORT" | None
    signal_direction: "LONG" | "SHORT" | None
    group_reputation: [0..1+] ölçeklenmiş itibar katsayısı
    """
    if not model_direction or not signal_direction:
        return 0.0
    agree = model_direction.upper() == signal_direction.upper()
    raw = max_bias if agree else -max_bias
    # itibar ile ölçekle
    return float(raw * max(group_reputation, 0.0))
