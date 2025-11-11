"""In-memory Unit of Work implementation"""

from ...adapters.repository.memory import (
    InMemoryOrderRepository,
    InMemoryPositionRepository,
    InMemoryAccountRepository,
    InMemoryMarketDataRepository,
)
from .base import AbstractUnitOfWork


class InMemoryUnitOfWork(AbstractUnitOfWork):
    """
    In-memory implementation of Unit of Work.

    Useful for testing and backtesting where we don't need actual persistence.
    """

    def __init__(self):
        self.orders = InMemoryOrderRepository()
        self.positions = InMemoryPositionRepository()
        self.accounts = InMemoryAccountRepository()
        self.market_data = InMemoryMarketDataRepository()
        self._committed = False

    def commit(self) -> None:
        """
        Commit changes.

        In-memory implementation doesn't need to do anything special.
        """
        self._committed = True

    def rollback(self) -> None:
        """
        Rollback changes.

        In-memory implementation would need to restore previous state.
        For simplicity, we just mark as not committed.
        """
        self._committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
