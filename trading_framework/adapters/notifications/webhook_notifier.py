"""
Webhook Notifier

Sends notifications to custom webhooks (Discord, custom APIs, etc.)
"""

import logging
import aiohttp
from typing import Dict, Any
from .base import AbstractNotifier, Notification


logger = logging.getLogger(__name__)


class WebhookNotifier(AbstractNotifier):
    """
    Generic webhook notifier.

    Can be used with Discord webhooks, custom APIs, or any HTTP endpoint.

    Configuration example:
        {
            "enabled": true,
            "url": "https://your-webhook-url.com",
            "method": "POST",  # POST or GET
            "headers": {
                "Content-Type": "application/json",
                "Authorization": "Bearer YOUR_TOKEN"
            },
            "format": "json",  # json, discord, or custom
            "min_level": "INFO"
        }

    For Discord webhooks:
        {
            "enabled": true,
            "url": "https://discord.com/api/webhooks/YOUR/WEBHOOK/ID",
            "format": "discord",
            "username": "Trading Bot",
            "avatar_url": "https://..."
        }
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize webhook notifier"""
        super().__init__("Webhook", config)

        self.url = config.get("url")
        self.method = config.get("method", "POST").upper()
        self.headers = config.get("headers", {"Content-Type": "application/json"})
        self.format = config.get("format", "json")

        # Discord-specific
        self.username = config.get("username", "Trading Bot")
        self.avatar_url = config.get("avatar_url")

        if not self.url:
            logger.warning("Webhook notifier configured but no URL provided")

    async def send(self, notification: Notification) -> bool:
        """Send webhook notification"""
        if not self.url:
            logger.warning("Webhook URL not configured")
            return False

        try:
            if self.format == "discord":
                payload = self._format_discord(notification)
            else:
                payload = notification.to_dict()

            async with aiohttp.ClientSession() as session:
                if self.method == "POST":
                    async with session.post(
                        self.url,
                        json=payload,
                        headers=self.headers
                    ) as response:
                        success = 200 <= response.status < 300
                elif self.method == "GET":
                    async with session.get(
                        self.url,
                        params=payload,
                        headers=self.headers
                    ) as response:
                        success = 200 <= response.status < 300
                else:
                    logger.error(f"Unsupported HTTP method: {self.method}")
                    return False

                if success:
                    logger.info(f"Webhook notification sent: {notification.title}")
                    return True
                else:
                    error_text = await response.text()
                    logger.error(f"Webhook request failed: {error_text}")
                    return False

        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}", exc_info=True)
            return False

    def _format_discord(self, notification: Notification) -> Dict[str, Any]:
        """Format notification for Discord webhook"""
        from .base import NotificationLevel

        # Color mapping (Discord uses decimal colors)
        color_map = {
            NotificationLevel.INFO: 1752220,  # Blue
            NotificationLevel.SUCCESS: 3066993,  # Green
            NotificationLevel.WARNING: 16776960,  # Yellow
            NotificationLevel.ERROR: 15158332,  # Red
            NotificationLevel.CRITICAL: 15158332,  # Red
        }

        color = color_map.get(notification.level, 9807270)  # Gray

        # Build embed
        embed = {
            "title": notification.title,
            "description": notification.message if notification.message else None,
            "color": color,
            "timestamp": notification.timestamp.isoformat(),
        }

        # Add fields for data
        if notification.data:
            fields = []
            for key, value in list(notification.data.items())[:25]:  # Discord limit
                fields.append({
                    "name": key.replace("_", " ").title(),
                    "value": str(value),
                    "inline": True
                })
            embed["fields"] = fields

        # Add footer
        if notification.source:
            embed["footer"] = {"text": notification.source}

        # Build payload
        payload = {
            "embeds": [embed],
            "username": self.username,
        }

        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url

        return payload
