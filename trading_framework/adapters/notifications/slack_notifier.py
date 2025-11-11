"""
Slack Notifier

Sends notifications via Slack Incoming Webhooks.
"""

import logging
import aiohttp
from typing import Dict, Any
from .base import AbstractNotifier, Notification


logger = logging.getLogger(__name__)


class SlackNotifier(AbstractNotifier):
    """
    Slack notifier using Incoming Webhooks.

    Configuration example:
        {
            "enabled": true,
            "webhook_url": "https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
            "channel": "#trading-alerts",  # optional
            "username": "Trading Bot",  # optional
            "icon_emoji": ":chart_with_upwards_trend:",  # optional
            "min_level": "WARNING"
        }

    To get webhook URL:
        1. Go to your Slack workspace settings
        2. Apps -> Incoming Webhooks
        3. Add Configuration
        4. Choose channel and copy webhook URL
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize Slack notifier"""
        super().__init__("Slack", config)

        self.webhook_url = config.get("webhook_url")
        self.channel = config.get("channel")
        self.username = config.get("username", "Trading Bot")
        self.icon_emoji = config.get("icon_emoji", ":chart_with_upwards_trend:")

        if not self.webhook_url:
            logger.warning("Slack notifier configured but no webhook_url provided")

    async def send(self, notification: Notification) -> bool:
        """Send Slack notification"""
        if not self.webhook_url:
            logger.warning("Slack webhook_url not configured")
            return False

        try:
            payload = self._build_payload(notification)

            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    if response.status == 200:
                        logger.info(f"Slack notification sent: {notification.title}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send Slack notification: {error_text}")
                        return False

        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}", exc_info=True)
            return False

    def _build_payload(self, notification: Notification) -> Dict[str, Any]:
        """Build Slack message payload"""
        from .base import NotificationLevel

        # Color mapping
        color_map = {
            NotificationLevel.INFO: "#17a2b8",
            NotificationLevel.SUCCESS: "good",  # Slack built-in green
            NotificationLevel.WARNING: "warning",  # Slack built-in yellow
            NotificationLevel.ERROR: "danger",  # Slack built-in red
            NotificationLevel.CRITICAL: "danger",
        }

        # Emoji mapping
        emoji_map = {
            NotificationLevel.INFO: ":information_source:",
            NotificationLevel.SUCCESS: ":white_check_mark:",
            NotificationLevel.WARNING: ":warning:",
            NotificationLevel.ERROR: ":x:",
            NotificationLevel.CRITICAL: ":rotating_light:",
        }

        color = color_map.get(notification.level, "#6c757d")
        emoji = emoji_map.get(notification.level, ":bell:")

        # Build attachment
        attachment = {
            "color": color,
            "title": f"{emoji} {notification.title}",
            "text": notification.message if notification.message else None,
            "footer": notification.source if notification.source else "Trading Framework",
            "ts": int(notification.timestamp.timestamp()),
        }

        # Add fields for data
        if notification.data:
            fields = []
            for key, value in notification.data.items():
                fields.append({
                    "title": key.replace("_", " ").title(),
                    "value": str(value),
                    "short": True
                })
            attachment["fields"] = fields

        # Build payload
        payload = {
            "attachments": [attachment],
            "username": self.username,
            "icon_emoji": self.icon_emoji,
        }

        if self.channel:
            payload["channel"] = self.channel

        return payload
