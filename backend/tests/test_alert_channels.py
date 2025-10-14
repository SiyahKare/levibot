from backend.src.alerts.channels import (
    SEVERITY_COLORS,
    format_discord,
    format_slack,
    route_targets,
)


def test_format_slack_basic():
    alert = {
        "title": "High-Confidence BUY",
        "summary": "BTC/USDT signal @60000 (conf 0.84)",
        "severity": "high",
        "source": "signals",
        "labels": {"symbol": "BTC/USDT", "side": "buy", "conf": "0.84"},
    }
    payload = format_slack(alert)
    assert "blocks" in payload
    assert len(payload["blocks"]) >= 3  # section + fields + context
    # Check title in first block
    assert "High-Confidence BUY" in payload["blocks"][0]["text"]["text"]
    # Check context footer
    context_block = [b for b in payload["blocks"] if b["type"] == "context"][0]
    assert "high" in context_block["elements"][0]["text"].lower()


def test_format_discord_basic():
    alert = {
        "title": "Risk Engine Blocked",
        "summary": "Order blocked due to cooldown",
        "severity": "medium",
        "source": "risk",
        "labels": {"symbol": "ETH/USDT", "reason": "cooldown"},
    }
    payload = format_discord(alert)
    assert "embeds" in payload
    embed = payload["embeds"][0]
    assert embed["title"] == "Risk Engine Blocked"
    assert embed["description"] == "Order blocked due to cooldown"
    assert embed["color"] == SEVERITY_COLORS["medium"]
    assert "fields" in embed
    assert len(embed["fields"]) == 2  # symbol + reason


def test_severity_colors():
    for severity in ["info", "low", "medium", "high", "critical"]:
        alert = {"title": "Test", "summary": "...", "severity": severity}
        payload = format_discord(alert)
        embed = payload["embeds"][0]
        assert embed["color"] == SEVERITY_COLORS[severity]


def test_fallback_unknown_severity():
    alert = {"title": "Test", "summary": "...", "severity": "unknown"}
    payload = format_discord(alert)
    embed = payload["embeds"][0]
    # Should fallback to "info" color
    assert embed["color"] == SEVERITY_COLORS["info"]


def test_route_targets_both():
    env = {
        "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/xxx",
        "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/yyy",
    }
    targets = route_targets(env)
    assert "slack" in targets
    assert "discord" in targets


def test_route_targets_only_slack():
    env = {
        "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/xxx",
        "DISCORD_WEBHOOK_URL": "",
    }
    targets = route_targets(env)
    assert targets == ["slack"]


def test_route_targets_explicit_override():
    env = {
        "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/xxx",
        "DISCORD_WEBHOOK_URL": "https://discord.com/api/webhooks/yyy",
        "ALERT_DEFAULT_TARGETS": "discord",  # Only discord explicitly
    }
    targets = route_targets(env)
    assert targets == ["discord"]


def test_route_targets_explicit_invalid():
    env = {
        "SLACK_WEBHOOK_URL": "https://hooks.slack.com/services/xxx",
        "DISCORD_WEBHOOK_URL": "",
        "ALERT_DEFAULT_TARGETS": "discord",  # Discord not configured
    }
    targets = route_targets(env)
    assert targets == []  # Discord requested but URL missing
