"""
Console Notifier

Prints notifications to console/stdout. Useful for testing and development.
"""

import logging
from typing import Dict, Any
from .base import AbstractNotifier, Notification


logger = logging.getLogger(__name__)


class ConsoleNotifier(AbstractNotifier):
    """
    Console/stdout notifier.

    Prints formatted notifications to console.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize console notifier.

        Config options:
            enabled: Enable/disable (default: True)
            min_level: Minimum notification level (default: INFO)
            colored: Use colored output if available (default: True)
        """
        super().__init__("Console", config)
        self.colored = config.get("colored", True)

        # Try to import colorama for colored output
        self.use_colors = False
        if self.colored:
            try:
                from colorama import init, Fore, Style
                init(autoreset=True)
                self.Fore = Fore
                self.Style = Style
                self.use_colors = True
            except ImportError:
                logger.debug("colorama not available, using plain console output")

    async def send(self, notification: Notification) -> bool:
        """Print notification to console"""
        try:
            if self.use_colors:
                self._print_colored(notification)
            else:
                self._print_plain(notification)
            return True
        except Exception as e:
            logger.error(f"Error printing to console: {e}")
            return False

    def _print_colored(self, notification: Notification) -> None:
        """Print with colors"""
        from .base import NotificationLevel

        # Color mapping
        color_map = {
            NotificationLevel.INFO: self.Fore.CYAN,
            NotificationLevel.SUCCESS: self.Fore.GREEN,
            NotificationLevel.WARNING: self.Fore.YELLOW,
            NotificationLevel.ERROR: self.Fore.RED,
            NotificationLevel.CRITICAL: self.Fore.RED + self.Style.BRIGHT,
        }

        color = color_map.get(notification.level, self.Fore.WHITE)

        print("\n" + "="*60)
        print(f"{color}[{notification.level.value}] {notification.title}{self.Style.RESET_ALL}")
        print(f"Time: {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")

        if notification.message:
            print(f"\n{notification.message}")

        if notification.data:
            print("\nDetails:")
            for key, value in notification.data.items():
                print(f"  {key}: {value}")

        if notification.source:
            print(f"\nSource: {notification.source}")

        print("="*60)

    def _print_plain(self, notification: Notification) -> None:
        """Print without colors"""
        print("\n" + notification.format_for_display())
