"""
Example: Running a Backtest with Notifications

Demonstrates how to set up and use the notification system to receive
alerts via Email, Telegram, Slack, Console, or Webhooks when trades execute.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_framework.domain.model import Asset, AssetType, BarResolution
from trading_framework.adapters.data_sources.csv import CSVDataSource
from trading_framework.adapters.notifications import (
    NotificationManager,
    ConsoleNotifier,
    EmailNotifier,
    TelegramNotifier,
    SlackNotifier,
    WebhookNotifier,
)
from trading_framework.entrypoints.backtesting import BacktestEngine, BacktestConfig
from strategies.simple_sma_crossover import SimpleSMACrossover


async def main():
    """Run a backtest with comprehensive notifications"""

    print("="*60)
    print("TRADING FRAMEWORK - BACKTEST WITH NOTIFICATIONS")
    print("="*60)

    # Define the asset to trade
    asset = Asset(
        symbol="AAPL",
        asset_type=AssetType.STOCK,
        exchange="NASDAQ",
        currency="USD",
        min_quantity=Decimal("1"),
        quantity_increment=Decimal("1"),
        min_price_increment=Decimal("0.01"),
    )

    # Configure data source
    data_source = CSVDataSource({
        "data_dir": "./data",
        "filename_pattern": "{symbol}_{resolution}.csv",
        "date_format": "%Y-%m-%d %H:%M:%S"
    })

    # =========================================================================
    # SETUP NOTIFICATION SYSTEM
    # =========================================================================

    # Create notification manager
    notification_manager = NotificationManager()

    # 1. Console Notifier (always enabled for demo)
    console_notifier = ConsoleNotifier({
        "enabled": True,
        "min_level": "INFO",  # Show all notifications
        "colored": True,
    })
    notification_manager.add_notifier(console_notifier)

    # 2. Email Notifier (configure with your SMTP settings)
    # Uncomment and configure to enable email notifications
    """
    email_notifier = EmailNotifier({
        "enabled": True,
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_user": "your_email@gmail.com",
        "smtp_password": "your_app_password",  # Use app password for Gmail
        "from_email": "your_email@gmail.com",
        "to_emails": ["recipient@example.com"],
        "use_tls": True,
        "min_level": "SUCCESS",  # Only send successful trades and above
    })
    notification_manager.add_notifier(email_notifier)
    """

    # 3. Telegram Notifier
    # Get bot token from @BotFather
    # Get chat_id from https://api.telegram.org/bot<TOKEN>/getUpdates
    """
    telegram_notifier = TelegramNotifier({
        "enabled": True,
        "bot_token": "YOUR_BOT_TOKEN",
        "chat_ids": ["YOUR_CHAT_ID"],
        "parse_mode": "HTML",
        "min_level": "SUCCESS",  # Only trades and important alerts
    })
    notification_manager.add_notifier(telegram_notifier)
    """

    # 4. Slack Notifier
    # Get webhook URL from Slack Incoming Webhooks app
    """
    slack_notifier = SlackNotifier({
        "enabled": True,
        "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
        "channel": "#trading-alerts",
        "username": "Trading Bot",
        "icon_emoji": ":chart_with_upwards_trend:",
        "min_level": "WARNING",  # Only warnings and errors
    })
    notification_manager.add_notifier(slack_notifier)
    """

    # 5. Discord Webhook (using generic webhook notifier)
    """
    discord_notifier = WebhookNotifier({
        "enabled": True,
        "url": "https://discord.com/api/webhooks/YOUR/WEBHOOK/ID",
        "format": "discord",
        "username": "Trading Bot",
        "min_level": "INFO",
    })
    notification_manager.add_notifier(discord_notifier)
    """

    # 6. Custom Webhook (send to your own API)
    """
    custom_webhook = WebhookNotifier({
        "enabled": True,
        "url": "https://your-api.com/trading/notifications",
        "method": "POST",
        "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer YOUR_TOKEN"
        },
        "format": "json",
        "min_level": "INFO",
    })
    notification_manager.add_notifier(custom_webhook)
    """

    print(f"\nNotification channels configured:")
    print(f"  Total notifiers: {len(notification_manager.notifiers)}")
    for notifier in notification_manager.notifiers:
        status = "✅ Enabled" if notifier.enabled else "❌ Disabled"
        print(f"  - {notifier.name}: {status} (min_level: {notifier.min_level.value})")

    # =========================================================================
    # CONFIGURE BACKTEST
    # =========================================================================

    config = BacktestConfig(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        assets=[asset],
        resolution=BarResolution.DAY_1,
        initial_capital=Decimal("100000"),
        commission_per_share=Decimal("0.01"),
        slippage_pct=Decimal("0.001"),
        # Enable notifications!
        enable_notifications=True,
        notification_manager=notification_manager,
    )

    # Create strategy
    strategy = SimpleSMACrossover(
        fast_period=10,
        slow_period=30,
        position_size_pct=0.5
    )

    # =========================================================================
    # RUN BACKTEST
    # =========================================================================

    print(f"\nRunning backtest with notifications enabled...")
    print(f"Asset: {asset.symbol}")
    print(f"Period: {config.start_date} to {config.end_date}")
    print(f"Strategy: SMA Crossover (10/30)")
    print("\nYou will receive notifications for:")
    print("  ✅ Trade executions")
    print("  ⚠️  Order rejections")
    print("  📊 Backtest completion summary")

    engine = BacktestEngine(
        config=config,
        data_source=data_source,
        strategy=strategy,
    )

    # Run backtest
    print("\n" + "="*60)
    result = await engine.run()

    # Print results
    result.print_summary()

    # Print notification statistics
    print("\n" + "="*60)
    print("NOTIFICATION STATISTICS")
    print("="*60)

    stats = notification_manager.get_statistics()
    print(f"\nTotal Notifications Sent: {stats['total']}")

    if stats.get('by_level'):
        print("\nBy Level:")
        for level, count in stats['by_level'].items():
            print(f"  {level}: {count}")

    if stats.get('by_source'):
        print("\nBy Source:")
        for source, count in stats['by_source'].items():
            print(f"  {source}: {count}")

    print(f"\nNotifiers: {stats['enabled_notifiers']}/{stats['notifiers_count']} enabled")
    print("="*60)

    return result


if __name__ == "__main__":
    # Run the async main function
    result = asyncio.run(main())

    if result.total_return > 0:
        print("\n✅ Strategy was profitable!")
    else:
        print("\n❌ Strategy lost money")

    print("\n💡 TIP: Edit the notification configurations above to enable")
    print("   Email, Telegram, Slack, or Discord notifications!")
    print("\n📚 See documentation for setup instructions:")
    print("   - Telegram: Talk to @BotFather to create a bot")
    print("   - Slack: Enable Incoming Webhooks in your workspace")
    print("   - Email: Use app-specific passwords for Gmail")
    print("   - Discord: Create a webhook in Server Settings")
