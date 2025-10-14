"""
Telegram Bot - Command interface and alerts
Enterprise control center for LeviBot
"""
import asyncio
import os

# Import LeviBot components
import sys
from datetime import datetime

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from src.infra.event_bus import EventBus, publish_alert
from src.store.clickhouse_client import get_clickhouse_client
from src.strategies.policy_engine import get_policy_engine

# Configuration
BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
ADMIN_IDS = [int(x) for x in os.getenv("TG_ADMIN_IDS", "").split(",") if x]
MINI_APP_URL = os.getenv("TG_MINI_APP_URL", "https://levibot.app")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


# Global instances
event_bus = EventBus(REDIS_URL)
policy_engine = get_policy_engine(REDIS_URL)
clickhouse = get_clickhouse_client()


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command - show main menu"""
    keyboard = [
        [
            InlineKeyboardButton(
                "🎛️ Control Panel",
                web_app=WebAppInfo(url=MINI_APP_URL)
            )
        ],
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("💰 PnL", callback_data="pnl")
        ],
        [
            InlineKeyboardButton("🚨 Kill Switch", callback_data="killswitch"),
            InlineKeyboardButton("ℹ️ Help", callback_data="help")
        ]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🤖 *LeviBot Control Center*\n\n"
        "Enterprise AI trading platform\n"
        "Select an option below:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get system status"""
    try:
        # Get policy engine status
        status = await policy_engine.get_status()
        
        # Format message
        msg = (
            "📊 *System Status*\n\n"
            f"💰 Equity: ${status['equity']:,.2f}\n"
            f"📈 Daily PnL: ${status['daily_pnl']:+,.2f}\n"
            f"📉 Daily DD: {status['daily_dd_pct']:.2%}\n"
            f"🎯 Exposure: {status['exposure_pct']:.1%}\n"
            f"🔢 Positions: {status['num_positions']}\n"
            f"📊 Daily Trades: {status['daily_trades']}/{status['limits']['max_daily_trades']}\n\n"
        )
        
        if status['kill_switch']:
            msg += "🚨 *KILL SWITCH ACTIVE*\n"
        else:
            msg += "✅ Trading active\n"
        
        # Add position details
        if status['positions']:
            msg += "\n*Open Positions:*\n"
            for symbol, size in status['positions'].items():
                msg += f"  • {symbol}: ${size:,.0f}\n"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def pnl_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get PnL summary"""
    try:
        # Get equity curve from ClickHouse
        equity_curve = clickhouse.query_equity_curve(hours=24)
        
        if not equity_curve:
            await update.message.reply_text("📊 No PnL data available")
            return
        
        # Calculate stats
        start_equity = equity_curve[0]['equity']
        current_equity = equity_curve[-1]['equity']
        pnl_24h = current_equity - start_equity
        return_24h = (pnl_24h / start_equity) if start_equity > 0 else 0
        
        # Get recent signals
        signals = clickhouse.query_recent_signals(hours=24, limit=10)
        
        msg = (
            "💰 *24h Performance*\n\n"
            f"Starting: ${start_equity:,.2f}\n"
            f"Current: ${current_equity:,.2f}\n"
            f"PnL: ${pnl_24h:+,.2f} ({return_24h:+.2%})\n"
            f"Signals: {len(signals)}\n\n"
        )
        
        # Add recent signals
        if signals:
            msg += "*Recent Signals:*\n"
            for sig in signals[:5]:
                ts, symbol, strategy, side, conf, reason, _ = sig
                side_emoji = "🟢" if side > 0 else "🔴" if side < 0 else "⚪"
                msg += f"{side_emoji} {symbol} ({strategy}) - {conf:.2%}\n"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def killswitch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle kill switch (admin only)"""
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only")
        return
    
    try:
        status = await policy_engine.get_status()
        
        if status['kill_switch']:
            # Deactivate
            await policy_engine.deactivate_kill_switch()
            msg = "✅ Kill switch DEACTIVATED\nTrading resumed"
            
            # Publish alert
            await publish_alert(
                event_bus,
                level="info",
                title="Kill Switch Deactivated",
                message=f"By user {update.effective_user.username}"
            )
        else:
            # Activate
            await policy_engine.activate_kill_switch(
                reason=f"manual_by_{update.effective_user.username}"
            )
            msg = "🚨 Kill switch ACTIVATED\nAll new trades blocked"
            
            # Publish alert
            await publish_alert(
                event_bus,
                level="critical",
                title="Kill Switch Activated",
                message=f"By user {update.effective_user.username}"
            )
        
        await update.message.reply_text(msg)
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def strategies_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List active strategies"""
    try:
        # Query strategy stats from ClickHouse
        strategies = ["lse", "day", "swing", "rsi_macd"]
        
        msg = "🎯 *Active Strategies*\n\n"
        
        for strategy in strategies:
            try:
                stats = clickhouse.query_strategy_stats(strategy, days=7)
                msg += (
                    f"*{strategy.upper()}*\n"
                    f"  Signals (7d): {stats['num_signals']}\n"
                    f"  Long/Short: {stats['num_long']}/{stats['num_short']}\n"
                    f"  Avg Conf: {stats['avg_confidence']:.2%}\n\n"
                )
            except Exception:
                msg += f"*{strategy.upper()}*\n  No data\n\n"
        
        await update.message.reply_text(msg, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    msg = (
        "🤖 *LeviBot Commands*\n\n"
        "/start - Main menu\n"
        "/status - System status\n"
        "/pnl - PnL summary\n"
        "/killswitch - Emergency stop (admin)\n"
        "/strategies - Strategy stats\n"
        "/help - This message\n\n"
        "*Quick Actions:*\n"
        "• Use inline buttons for fast access\n"
        "• Open Control Panel for full features\n"
        "• Alerts sent automatically\n"
    )
    
    await update.message.reply_text(msg, parse_mode="Markdown")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "status":
        await status_command(query, context)
    elif query.data == "pnl":
        await pnl_command(query, context)
    elif query.data == "killswitch":
        await killswitch_command(query, context)
    elif query.data == "help":
        await help_command(query, context)


async def send_alert_to_admins(
    app: Application,
    level: str,
    title: str,
    message: str
):
    """Send alert to all admins"""
    emoji_map = {
        "critical": "🚨",
        "warning": "⚠️",
        "info": "ℹ️",
        "success": "✅"
    }
    
    emoji = emoji_map.get(level, "📢")
    
    alert_msg = (
        f"{emoji} *{title}*\n\n"
        f"{message}\n\n"
        f"_Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
    )
    
    for admin_id in ADMIN_IDS:
        try:
            await app.bot.send_message(
                chat_id=admin_id,
                text=alert_msg,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Failed to send alert to {admin_id}: {e}")


async def alert_listener(app: Application):
    """Listen for alerts from event bus and forward to Telegram"""
    print("🎧 Alert listener started")
    
    async for event in event_bus.subscribe("alerts", "telegram-bot"):
        try:
            payload = event.payload
            await send_alert_to_admins(
                app,
                level=payload.get("level", "info"),
                title=payload.get("title", "Alert"),
                message=payload.get("message", "")
            )
        except Exception as e:
            print(f"❌ Alert listener error: {e}")


def main():
    """Run bot"""
    if not BOT_TOKEN:
        print("❌ TG_BOT_TOKEN not set")
        return
    
    if not ADMIN_IDS:
        print("⚠️ TG_ADMIN_IDS not set - bot will have limited functionality")
    
    # Create application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("pnl", pnl_command))
    app.add_handler(CommandHandler("killswitch", killswitch_command))
    app.add_handler(CommandHandler("strategies", strategies_command))
    app.add_handler(CommandHandler("help", help_command))
    
    # Add callback handler
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Start alert listener in background
    asyncio.create_task(alert_listener(app))
    
    print("✅ LeviBot Telegram Bot started")
    print(f"   Admins: {ADMIN_IDS}")
    print(f"   Mini App: {MINI_APP_URL}")
    
    # Run bot
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

