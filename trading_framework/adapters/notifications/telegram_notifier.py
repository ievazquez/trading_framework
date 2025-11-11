"""
Telegram Notifier

Sends notifications via Telegram Bot API.
"""

import logging
import aiohttp
from typing import Dict, Any
from .base import AbstractNotifier, Notification


logger = logging.getLogger(__name__)


class TelegramNotifier(AbstractNotifier):
    """
    Telegram notifier using Bot API.

    Configuration example:
        {
            "enabled": true,
            "bot_token": "YOUR_BOT_TOKEN",
            "chat_ids": ["CHAT_ID_1", "CHAT_ID_2"],
            "parse_mode": "HTML",  # or "Markdown"
            "min_level": "INFO"
        }

    To get bot token:
        1. Talk to @BotFather on Telegram
        2. Create a new bot
        3. Copy the token

    To get chat_id:
        1. Start chat with your bot
        2. Visit: https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
        3. Look for "chat":{"id":...}
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize Telegram notifier"""
        super().__init__("Telegram", config)

        self.bot_token = config.get("bot_token")
        self.chat_ids = config.get("chat_ids", [])
        self.parse_mode = config.get("parse_mode", "HTML")

        if not self.bot_token:
            logger.warning("Telegram notifier configured but no bot_token provided")

        if not self.chat_ids:
            logger.warning("Telegram notifier configured but no chat_ids provided")

        self.api_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def send(self, notification: Notification) -> bool:
        """Send Telegram notification"""
        if not self.bot_token or not self.chat_ids:
            logger.warning("Telegram notifier not properly configured")
            return False

        try:
            message = self._format_message(notification)

            async with aiohttp.ClientSession() as session:
                success_count = 0

                for chat_id in self.chat_ids:
                    payload = {
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": self.parse_mode,
                    }

                    async with session.post(
                        f"{self.api_url}/sendMessage",
                        json=payload
                    ) as response:
                        if response.status == 200:
                            success_count += 1
                        else:
                            error_data = await response.text()
                            logger.error(
                                f"Failed to send to chat {chat_id}: {error_data}"
                            )

                if success_count > 0:
                    logger.info(
                        f"Telegram notification sent to {success_count}/{len(self.chat_ids)} chats"
                    )
                    return True

                return False

        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}", exc_info=True)
            return False

    def _format_message(self, notification: Notification) -> str:
        """Format notification for Telegram"""
        from .base import NotificationLevel

        # Emoji mapping
        emoji_map = {
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.SUCCESS: "✅",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.ERROR: "❌",
            NotificationLevel.CRITICAL: "🚨",
        }

        emoji = emoji_map.get(notification.level, "•")

        if self.parse_mode == "HTML":
            return self._format_html(notification, emoji)
        elif self.parse_mode == "Markdown":
            return self._format_markdown(notification, emoji)
        else:
            return notification.format_for_display()

    def _format_html(self, notification: Notification, emoji: str) -> str:
        """Format as HTML"""
        lines = [
            f"<b>{emoji} {notification.title}</b>",
            f"<i>{notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</i>",
            f"Level: <code>{notification.level.value}</code>",
        ]

        if notification.message:
            lines.append("")
            lines.append(notification.message)

        if notification.data:
            lines.append("")
            lines.append("<b>Details:</b>")
            for key, value in notification.data.items():
                lines.append(f"• <b>{key}:</b> {value}")

        if notification.source:
            lines.append("")
            lines.append(f"<i>Source: {notification.source}</i>")

        return "\n".join(lines)

    def _format_markdown(self, notification: Notification, emoji: str) -> str:
        """Format as Markdown"""
        lines = [
            f"**{emoji} {notification.title}**",
            f"_{notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}_",
            f"Level: `{notification.level.value}`",
        ]

        if notification.message:
            lines.append("")
            lines.append(notification.message)

        if notification.data:
            lines.append("")
            lines.append("**Details:**")
            for key, value in notification.data.items():
                lines.append(f"• **{key}:** {value}")

        if notification.source:
            lines.append("")
            lines.append(f"_Source: {notification.source}_")

        return "\n".join(lines)
