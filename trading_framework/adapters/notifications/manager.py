"""
Notification Manager

Coordinates multiple notification channels and routes notifications.
"""

import logging
import asyncio
from typing import List, Dict, Any
from .base import AbstractNotifier, Notification, NotificationLevel


logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Manages multiple notification channels.

    Routes notifications to appropriate channels based on configuration.
    """

    def __init__(self):
        """Initialize notification manager"""
        self.notifiers: List[AbstractNotifier] = []
        self.notification_history: List[Notification] = []
        self.max_history_size = 1000

    def add_notifier(self, notifier: AbstractNotifier) -> None:
        """
        Add a notification channel.

        Args:
            notifier: Notifier to add
        """
        self.notifiers.append(notifier)
        logger.info(f"Added notifier: {notifier.name}")

    def remove_notifier(self, name: str) -> bool:
        """
        Remove a notifier by name.

        Args:
            name: Name of notifier to remove

        Returns:
            True if removed
        """
        for i, notifier in enumerate(self.notifiers):
            if notifier.name == name:
                self.notifiers.pop(i)
                logger.info(f"Removed notifier: {name}")
                return True
        return False

    async def notify(self, notification: Notification) -> Dict[str, bool]:
        """
        Send notification to all applicable channels.

        Args:
            notification: Notification to send

        Returns:
            Dictionary mapping notifier name to success status
        """
        # Store in history
        self.notification_history.append(notification)
        if len(self.notification_history) > self.max_history_size:
            self.notification_history.pop(0)

        # Send to all notifiers concurrently
        results = {}
        tasks = []

        for notifier in self.notifiers:
            task = notifier.notify(notification)
            tasks.append((notifier.name, task))

        # Wait for all to complete
        for name, task in tasks:
            try:
                success = await task
                results[name] = success
                if success:
                    logger.debug(f"Notification sent via {name}: {notification.title}")
            except Exception as e:
                logger.error(f"Error sending notification via {name}: {e}", exc_info=True)
                results[name] = False

        return results

    async def notify_trade_executed(
        self,
        asset_symbol: str,
        side: str,
        quantity: float,
        price: float,
        order_id: str,
        **kwargs
    ) -> Dict[str, bool]:
        """
        Send trade execution notification.

        Convenience method for trade notifications.
        """
        notification = Notification(
            title=f"Trade Executed: {side} {asset_symbol}",
            message=f"Executed {side} order for {quantity} units at ${price:.2f}",
            level=NotificationLevel.SUCCESS,
            data={
                "asset": asset_symbol,
                "side": side,
                "quantity": quantity,
                "price": price,
                "order_id": order_id,
                **kwargs
            },
            tags=["trade", "execution", side.lower()],
            source="TradingSystem"
        )

        return await self.notify(notification)

    async def notify_order_rejected(
        self,
        asset_symbol: str,
        side: str,
        quantity: float,
        reason: str,
        order_id: str,
        **kwargs
    ) -> Dict[str, bool]:
        """Send order rejection notification"""
        notification = Notification(
            title=f"Order Rejected: {side} {asset_symbol}",
            message=f"Order rejected: {reason}",
            level=NotificationLevel.WARNING,
            data={
                "asset": asset_symbol,
                "side": side,
                "quantity": quantity,
                "reason": reason,
                "order_id": order_id,
                **kwargs
            },
            tags=["order", "rejection"],
            source="RiskManager"
        )

        return await self.notify(notification)

    async def notify_position_closed(
        self,
        asset_symbol: str,
        pnl: float,
        pnl_pct: float,
        quantity: float,
        entry_price: float,
        exit_price: float,
        **kwargs
    ) -> Dict[str, bool]:
        """Send position closed notification"""
        level = NotificationLevel.SUCCESS if pnl >= 0 else NotificationLevel.WARNING

        notification = Notification(
            title=f"Position Closed: {asset_symbol}",
            message=f"P&L: ${pnl:,.2f} ({pnl_pct:.2f}%)",
            level=level,
            data={
                "asset": asset_symbol,
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "quantity": quantity,
                "entry_price": entry_price,
                "exit_price": exit_price,
                **kwargs
            },
            tags=["position", "closed", "pnl"],
            source="TradingSystem"
        )

        return await self.notify(notification)

    async def notify_risk_violation(
        self,
        violation_type: str,
        message: str,
        current_value: float,
        limit_value: float,
        **kwargs
    ) -> Dict[str, bool]:
        """Send risk violation notification"""
        notification = Notification(
            title=f"Risk Violation: {violation_type}",
            message=message,
            level=NotificationLevel.ERROR,
            data={
                "violation_type": violation_type,
                "current_value": current_value,
                "limit_value": limit_value,
                **kwargs
            },
            tags=["risk", "violation"],
            source="RiskManager"
        )

        return await self.notify(notification)

    async def notify_daily_summary(
        self,
        pnl: float,
        pnl_pct: float,
        trades_count: int,
        win_rate: float,
        **kwargs
    ) -> Dict[str, bool]:
        """Send daily summary notification"""
        level = NotificationLevel.SUCCESS if pnl >= 0 else NotificationLevel.WARNING

        notification = Notification(
            title="Daily Trading Summary",
            message=f"P&L: ${pnl:,.2f} ({pnl_pct:.2f}%) | Trades: {trades_count} | Win Rate: {win_rate:.1f}%",
            level=level,
            data={
                "pnl": pnl,
                "pnl_pct": pnl_pct,
                "trades_count": trades_count,
                "win_rate": win_rate,
                **kwargs
            },
            tags=["summary", "daily"],
            source="TradingSystem"
        )

        return await self.notify(notification)

    async def notify_circuit_breaker(
        self,
        reason: str,
        loss_amount: float,
        loss_pct: float,
        **kwargs
    ) -> Dict[str, bool]:
        """Send circuit breaker alert"""
        notification = Notification(
            title="🚨 CIRCUIT BREAKER TRIGGERED",
            message=f"Trading halted: {reason}\nLoss: ${loss_amount:,.2f} ({loss_pct:.2f}%)",
            level=NotificationLevel.CRITICAL,
            data={
                "reason": reason,
                "loss_amount": loss_amount,
                "loss_pct": loss_pct,
                **kwargs
            },
            tags=["circuit_breaker", "critical", "risk"],
            source="RiskManager"
        )

        return await self.notify(notification)

    def get_statistics(self) -> Dict[str, Any]:
        """Get notification statistics"""
        if not self.notification_history:
            return {"total": 0}

        by_level = {}
        by_source = {}

        for notif in self.notification_history:
            # By level
            level = notif.level.value
            by_level[level] = by_level.get(level, 0) + 1

            # By source
            source = notif.source or "Unknown"
            by_source[source] = by_source.get(source, 0) + 1

        return {
            "total": len(self.notification_history),
            "by_level": by_level,
            "by_source": by_source,
            "notifiers_count": len(self.notifiers),
            "enabled_notifiers": len([n for n in self.notifiers if n.enabled]),
        }

    def clear_history(self) -> None:
        """Clear notification history"""
        self.notification_history.clear()
        logger.info("Notification history cleared")
