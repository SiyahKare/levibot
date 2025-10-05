from __future__ import annotations
import os
from typing import Dict, Any, Optional
from prometheus_client import Counter

from .rules import load_rules, evaluate
from .channels import deliver_alert_via, route_targets
from ..infra.metrics import registry

# Metric for auto-triggered alerts
alerts_triggered_total = Counter(
    "levibot_alerts_triggered_total",
    "Total alerts auto-triggered",
    ["source"],
    registry=registry
)


def should_auto_trigger() -> bool:
    """Check if auto-trigger is enabled."""
    return os.getenv("ALERT_AUTO_TRIGGER_ENABLED", "true").lower() == "true"


def min_confidence_threshold() -> float:
    """Get minimum confidence threshold for auto-trigger."""
    return float(os.getenv("ALERT_MIN_CONF", "0.8"))


def auto_trigger_from_signal(
    event: Dict[str, Any],
    queue,
    rules_path: str = "configs/alerts.yaml"
) -> Optional[Dict[str, str]]:
    """Auto-trigger alert if signal meets criteria.
    
    Args:
        event: Signal event dict (event_type, payload, etc.)
        queue: WebhookQueue instance
        rules_path: Path to alert rules YAML
    
    Returns:
        Dict with triggered info or None if not triggered
    """
    if not should_auto_trigger():
        return None
    
    # Load rules and evaluate
    try:
        rules = load_rules(rules_path)
        matches = evaluate(event, rules)
    except Exception:
        return None
    
    if not matches:
        return None
    
    # Get signal details
    payload = event.get("payload", {})
    label = payload.get("label", "UNKNOWN")
    confidence = payload.get("confidence", 0.0)
    text = payload.get("text", "")
    symbol = event.get("symbol", "")
    
    # Check confidence threshold
    min_conf = min_confidence_threshold()
    if confidence < min_conf:
        return None
    
    # Build alert
    alert = {
        "title": f"{label} Signal Detected",
        "summary": f"{symbol or 'Signal'}: {text[:100]}... (confidence: {confidence:.2f})",
        "severity": matches[0].severity,  # Use first matched rule's severity
        "source": "auto",
        "labels": {
            "label": label,
            "confidence": f"{confidence:.2f}",
            "symbol": symbol or "N/A",
            "rule": matches[0].id,
        },
    }
    
    # Deliver to all configured targets
    targets = route_targets()
    for target in targets:
        deliver_alert_via(target, alert, queue)
    
    # Increment metric
    alerts_triggered_total.labels(source="auto").inc()
    
    # Log to JSONL
    from ..app.routers.alerts import _log_alert
    _log_alert(alert)
    
    return {
        "triggered": "true",
        "targets": ",".join(targets),
        "rule": matches[0].id,
        "severity": matches[0].severity,
    }
