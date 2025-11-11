"""
Unit of Work Pattern

The Unit of Work pattern maintains a list of objects affected by a business
transaction and coordinates the writing out of changes.

It provides:
1. Transaction management (commit/rollback)
2. Repository access
3. Event collection from aggregates
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List

from ...domain.events.base import Event
from ...adapters.repository.base import (
    AbstractOrderRepository,
    AbstractPositionRepository,
    AbstractAccountRepository,
    AbstractMarketDataRepository,
)


class AbstractUnitOfWork(ABC):
    """
    Abstract Unit of Work.

    Manages a transaction and provides access to repositories.
    """

    # Repositories
    orders: AbstractOrderRepository
    positions: AbstractPositionRepository
    accounts: AbstractAccountRepository
    market_data: AbstractMarketDataRepository

    def __enter__(self) -> AbstractUnitOfWork:
        """Start a new unit of work"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """End the unit of work, rolling back on exception"""
        if exc_type is None:
            self.commit()
        else:
            self.rollback()

    @abstractmethod
    def commit(self) -> None:
        """
        Commit the transaction.

        Should also collect and return events from aggregates.
        """
        raise NotImplementedError

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the transaction"""
        raise NotImplementedError

    def collect_new_events(self) -> List[Event]:
        """
        Collect events from all tracked aggregates.

        This should be called after commit to publish domain events.
        """
        events = []

        # Collect from orders
        for order in self.orders.list():
            if hasattr(order, 'events') and order.events:
                events.extend(order.events)
                order.events.clear()

        # Collect from positions
        for position in self.positions.list():
            if hasattr(position, 'events') and position.events:
                events.extend(position.events)
                position.events.clear()

        # Collect from accounts
        for account in self.accounts.list():
            if hasattr(account, 'events') and account.events:
                events.extend(account.events)
                account.events.clear()

        return events
