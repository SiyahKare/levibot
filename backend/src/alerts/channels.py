from __future__ import annotations
import os
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

# Severity → color mapping
SEVERITY_COLORS = {
    "info": 0x3498db,      # blue
    "low": 0x95a5a6,       # gray
    "medium": 0xf39c12,    # orange
    "high": 0xe67e22,      # dark orange
    "critical": 0xe74c3c,  # red
}

def format_slack(alert: Dict[str, Any]) -> Dict[str, Any]:
    """Format alert for Slack Blocks API."""
    title = alert.get("title", "Alert")
    summary = alert.get("summary", "")
    severity = alert.get("severity", "info")
    source = alert.get("source", "system")
    labels = alert.get("labels", {})
    url = alert.get("url")
    
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{title}*\n{summary}"
            }
        }
    ]
    
    # Add fields if labels exist
    if labels:
        fields = []
        for k, v in labels.items():
            fields.append({"type": "mrkdwn", "text": f"*{k}*: {v}"})
        blocks.append({
            "type": "section",
            "fields": fields[:10]  # Slack max 10 fields
        })
    
    # Context footer
    context_text = f"Source: {source} | Severity: {severity.upper()}"
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": context_text}]
    })
    
    # Optional URL button
    if url:
        blocks.append({
            "type": "actions",
            "elements": [{
                "type": "button",
                "text": {"type": "plain_text", "text": "View Details"},
                "url": url
            }]
        })
    
    return {"blocks": blocks}


def format_discord(alert: Dict[str, Any]) -> Dict[str, Any]:
    """Format alert for Discord Embeds."""
    title = alert.get("title", "Alert")
    summary = alert.get("summary", "")
    severity = alert.get("severity", "info")
    source = alert.get("source", "system")
    labels = alert.get("labels", {})
    url = alert.get("url")
    
    color = SEVERITY_COLORS.get(severity.lower(), SEVERITY_COLORS["info"])
    
    embed = {
        "title": title,
        "description": summary,
        "color": color,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "footer": {
            "text": f"Source: {source} | Severity: {severity.upper()}"
        }
    }
    
    # Add fields if labels exist
    if labels:
        fields = []
        for k, v in list(labels.items())[:25]:  # Discord max 25 fields
            fields.append({"name": k, "value": str(v), "inline": True})
        embed["fields"] = fields
    
    # Optional URL
    if url:
        embed["url"] = url
    
    return {"embeds": [embed]}


def route_targets(env: Dict[str, str] | None = None) -> List[str]:
    """Determine active alert targets from environment."""
    if env is None:
        env = os.environ
    
    targets = []
    slack_url = env.get("SLACK_WEBHOOK_URL", "").strip()
    discord_url = env.get("DISCORD_WEBHOOK_URL", "").strip()
    telegram_bot_token = env.get("TELEGRAM_BOT_TOKEN", "").strip()
    telegram_alert_chat = env.get("TELEGRAM_ALERT_CHAT_ID", "").strip()
    
    if slack_url:
        targets.append("slack")
    if discord_url:
        targets.append("discord")
    if telegram_bot_token and telegram_alert_chat:
        targets.append("telegram")
    
    # Optional explicit targets override
    default_targets = env.get("ALERT_DEFAULT_TARGETS", "").strip()
    if default_targets:
        explicit = [t.strip().lower() for t in default_targets.split(",") if t.strip()]
        # Only include targets that have URLs configured
        targets = [t for t in explicit if 
                  (t == "slack" and slack_url) or 
                  (t == "discord" and discord_url) or
                  (t == "telegram" and telegram_bot_token and telegram_alert_chat)]
    
    return targets


def format_telegram(alert: Dict[str, Any]) -> str:
    """Format alert for Telegram."""
    title = alert.get("title", "Alert")
    summary = alert.get("summary", "")
    severity = alert.get("severity", "info")
    source = alert.get("source", "system")
    labels = alert.get("labels", {})
    
    # Severity emoji mapping
    severity_emoji = {
        "info": "ℹ️",
        "low": "🔵",
        "medium": "🟡",
        "high": "🟠",
        "critical": "🔴",
    }
    emoji = severity_emoji.get(severity.lower(), "ℹ️")
    
    lines = [
        f"{emoji} *{title}*",
        f"",
        f"{summary}",
        f"",
        f"📊 *Source:* {source}",
        f"⚠️ *Severity:* {severity.upper()}",
    ]
    
    if labels:
        lines.append("")
        lines.append("🏷️ *Labels:*")
        for k, v in list(labels.items())[:10]:
            lines.append(f"  • {k}: {v}")
    
    return "\n".join(lines)


def deliver_alert_via(target: str, alert: Dict[str, Any], queue) -> None:
    """Format and enqueue alert to specified target.
    
    Args:
        target: "slack", "discord", or "telegram"
        alert: Alert dictionary with title, summary, severity, labels, etc.
        queue: WebhookQueue instance (from main.py WEBHOOK_QUEUE)
    """
    env = os.environ
    
    if target == "slack":
        url = env.get("SLACK_WEBHOOK_URL", "").strip()
        if not url:
            return
        try:
            payload = format_slack(alert)
        except Exception:
            # Fallback to plain text
            payload = {"text": f"{alert.get('title', 'Alert')}: {alert.get('summary', '')}"}
        queue.enqueue(target_url=url, payload=payload, target_key="slack")
    
    elif target == "discord":
        url = env.get("DISCORD_WEBHOOK_URL", "").strip()
        if not url:
            return
        try:
            payload = format_discord(alert)
        except Exception:
            # Fallback to plain text
            payload = {"content": f"{alert.get('title', 'Alert')}: {alert.get('summary', '')}"}
        queue.enqueue(target_url=url, payload=payload, target_key="discord")
    
    elif target == "telegram":
        # Telegram uses direct bot API, not webhook queue
        try:
            from ..alerts.notify import send as send_telegram
            text = format_telegram(alert)
            send_telegram(text)
        except Exception:
            pass  # Silently fail for Telegram

