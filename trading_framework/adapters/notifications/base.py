"""
Base Notification System

Abstract interface for notification adapters supporting multiple channels
(email, Telegram, Slack, webhooks, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
import uuid


class NotificationLevel(Enum):
    """Notification severity levels"""
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class Notification:
    """Represents a notification to be sent"""

    # Identity
    notification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Content
    title: str = ""
    message: str = ""
    level: NotificationLevel = NotificationLevel.INFO

    # Rich content
    data: Dict[str, Any] = field(default_factory=dict)

    # Metadata
    tags: list = field(default_factory=list)
    source: Optional[str] = None  # e.g., "BacktestEngine", "RiskManager"

    def __str__(self) -> str:
        return f"[{self.level.value}] {self.title}: {self.message}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "notification_id": self.notification_id,
            "timestamp": self.timestamp.isoformat(),
            "title": self.title,
            "message": self.message,
            "level": self.level.value,
            "data": self.data,
            "tags": self.tags,
            "source": self.source,
        }

    def format_for_display(self) -> str:
        """Format notification for human-readable display"""
        emoji_map = {
            NotificationLevel.INFO: "ℹ️",
            NotificationLevel.SUCCESS: "✅",
            NotificationLevel.WARNING: "⚠️",
            NotificationLevel.ERROR: "❌",
            NotificationLevel.CRITICAL: "🚨",
        }

        emoji = emoji_map.get(self.level, "•")
        lines = [
            f"{emoji} {self.title}",
            f"Time: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Level: {self.level.value}",
        ]

        if self.message:
            lines.append(f"\n{self.message}")

        if self.data:
            lines.append("\nDetails:")
            for key, value in self.data.items():
                lines.append(f"  {key}: {value}")

        if self.source:
            lines.append(f"\nSource: {self.source}")

        return "\n".join(lines)


class AbstractNotifier(ABC):
    """
    Base class for all notification adapters.

    Each notifier implements sending notifications through a specific channel.
    """

    def __init__(self, name: str, config: Dict[str, Any]):
        """
        Initialize notifier.

        Args:
            name: Notifier name
            config: Configuration dictionary
        """
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)

        # Filter by level
        self.min_level = NotificationLevel[config.get("min_level", "INFO")]

        # Filter by tags
        self.include_tags = config.get("include_tags", [])
        self.exclude_tags = config.get("exclude_tags", [])

    def should_notify(self, notification: Notification) -> bool:
        """
        Check if this notification should be sent based on filters.

        Args:
            notification: Notification to check

        Returns:
            True if notification should be sent
        """
        if not self.enabled:
            return False

        # Check level filter
        level_priority = {
            NotificationLevel.INFO: 0,
            NotificationLevel.SUCCESS: 1,
            NotificationLevel.WARNING: 2,
            NotificationLevel.ERROR: 3,
            NotificationLevel.CRITICAL: 4,
        }

        if level_priority[notification.level] < level_priority[self.min_level]:
            return False

        # Check tag filters
        if self.include_tags:
            if not any(tag in notification.tags for tag in self.include_tags):
                return False

        if self.exclude_tags:
            if any(tag in notification.tags for tag in self.exclude_tags):
                return False

        return True

    @abstractmethod
    async def send(self, notification: Notification) -> bool:
        """
        Send notification through this channel.

        Args:
            notification: Notification to send

        Returns:
            True if sent successfully
        """
        raise NotImplementedError

    async def notify(self, notification: Notification) -> bool:
        """
        Check filters and send notification if applicable.

        Args:
            notification: Notification to send

        Returns:
            True if sent successfully
        """
        if not self.should_notify(notification):
            return False

        return await self.send(notification)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled})"
