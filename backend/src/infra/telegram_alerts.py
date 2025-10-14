"""
Telegram Alerts for Critical Events
Sends alerts for guardrails, cooldown, kill switch, and model fallback events
"""
import os

import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ALERT_CHAT_ID = os.getenv("TELEGRAM_ALERT_CHAT_ID", "")


def send_telegram_alert(message: str, priority: str = "INFO") -> bool:
    """
    Send alert to Telegram channel.
    
    Args:
        message: Alert message
        priority: INFO, WARNING, CRITICAL
    
    Returns:
        True if sent successfully
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_ALERT_CHAT_ID:
        # Telegram not configured, skip
        return False
    
    emoji = {
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "CRITICAL": "🚨"
    }.get(priority, "📢")
    
    formatted_message = f"{emoji} **LeviBot Alert**\n\n{message}"
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_ALERT_CHAT_ID,
            "text": formatted_message,
            "parse_mode": "Markdown"
        }
        resp = requests.post(url, json=payload, timeout=5)
        return resp.status_code == 200
    except Exception:
        # Silent fail - don't block operations
        return False


def alert_guardrails_rejection(symbol: str, confidence: float, threshold: float) -> None:
    """Alert when trade is rejected by guardrails."""
    message = (
        f"**Guardrails Rejection**\n"
        f"Symbol: `{symbol}`\n"
        f"Confidence: `{confidence:.3f}`\n"
        f"Threshold: `{threshold:.3f}`\n"
        f"Action: Trade blocked"
    )
    send_telegram_alert(message, "WARNING")


def alert_cooldown_triggered(minutes: int, reason: str = "manual") -> None:
    """Alert when cooldown is triggered."""
    message = (
        f"**Cooldown Triggered**\n"
        f"Duration: `{minutes} minutes`\n"
        f"Reason: `{reason}`\n"
        f"All trading paused"
    )
    send_telegram_alert(message, "WARNING")


def alert_cooldown_cleared() -> None:
    """Alert when cooldown is cleared."""
    message = "**Cooldown Cleared**\n" "Trading resumed"
    send_telegram_alert(message, "INFO")


def alert_kill_switch_activated(reason: str = "manual") -> None:
    """Alert when kill switch is activated."""
    message = (
        f"**🔴 KILL SWITCH ACTIVATED**\n"
        f"Reason: `{reason}`\n"
        f"All trading STOPPED\n"
        f"Manual intervention required"
    )
    send_telegram_alert(message, "CRITICAL")


def alert_kill_switch_deactivated() -> None:
    """Alert when kill switch is deactivated."""
    message = "**🟢 Kill Switch Deactivated**\n" "Trading enabled"
    send_telegram_alert(message, "INFO")


def alert_model_fallback(from_model: str, to_model: str, reason: str = "error") -> None:
    """Alert when model falls back."""
    message = (
        f"**Model Fallback**\n"
        f"From: `{from_model}`\n"
        f"To: `{to_model}`\n"
        f"Reason: `{reason}`\n"
        f"Check model health"
    )
    send_telegram_alert(message, "CRITICAL")


def alert_circuit_breaker_triggered(latency_ms: float, threshold_ms: int) -> None:
    """Alert when circuit breaker triggers."""
    message = (
        f"**Circuit Breaker Triggered**\n"
        f"Latency: `{latency_ms:.1f}ms`\n"
        f"Threshold: `{threshold_ms}ms`\n"
        f"Trading paused for performance"
    )
    send_telegram_alert(message, "WARNING")


def alert_daily_loss_limit(current_loss: float, limit: float) -> None:
    """Alert when approaching or hitting daily loss limit."""
    message = (
        f"**Daily Loss Limit Alert**\n"
        f"Current Loss: `${current_loss:.2f}`\n"
        f"Limit: `${limit:.2f}`\n"
        f"Trading may be halted"
    )
    send_telegram_alert(message, "CRITICAL")

