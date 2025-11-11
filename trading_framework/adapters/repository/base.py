"""
Base repository interfaces using the Repository Pattern.

Repositories abstract data persistence and retrieval, allowing the domain
to remain independent of infrastructure concerns.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict
from decimal import Decimal

from ...domain.model import (
    Asset,
    Order,
    Position,
    Account,
    Bar,
    Tick,
    BarResolution,
)


class AbstractRepository(ABC):
    """Base repository interface"""

    @abstractmethod
    def add(self, entity) -> None:
        """Add an entity to the repository"""
        raise NotImplementedError

    @abstractmethod
    def get(self, entity_id: str):
        """Retrieve an entity by ID"""
        raise NotImplementedError

    @abstractmethod
    def list(self) -> List:
        """List all entities"""
        raise NotImplementedError


class AbstractOrderRepository(AbstractRepository):
    """Repository for Order aggregates"""

    @abstractmethod
    def add(self, order: Order) -> None:
        """Add an order"""
        pass

    @abstractmethod
    def get(self, order_id: str) -> Optional[Order]:
        """Get order by ID"""
        pass

    @abstractmethod
    def get_by_broker_id(self, broker_order_id: str) -> Optional[Order]:
        """Get order by broker's order ID"""
        pass

    @abstractmethod
    def list(self, account_id: Optional[str] = None) -> List[Order]:
        """List all orders, optionally filtered by account"""
        pass

    @abstractmethod
    def list_active(self, account_id: Optional[str] = None) -> List[Order]:
        """List active orders"""
        pass

    @abstractmethod
    def update(self, order: Order) -> None:
        """Update an existing order"""
        pass


class AbstractPositionRepository(AbstractRepository):
    """Repository for Position aggregates"""

    @abstractmethod
    def add(self, position: Position) -> None:
        """Add a position"""
        pass

    @abstractmethod
    def get(self, position_id: str) -> Optional[Position]:
        """Get position by ID"""
        pass

    @abstractmethod
    def get_by_asset(self, account_id: str, asset: Asset) -> Optional[Position]:
        """Get position for a specific asset in an account"""
        pass

    @abstractmethod
    def list(self, account_id: Optional[str] = None) -> List[Position]:
        """List all positions, optionally filtered by account"""
        pass

    @abstractmethod
    def list_open(self, account_id: Optional[str] = None) -> List[Position]:
        """List open positions"""
        pass

    @abstractmethod
    def update(self, position: Position) -> None:
        """Update an existing position"""
        pass


class AbstractAccountRepository(AbstractRepository):
    """Repository for Account aggregates"""

    @abstractmethod
    def add(self, account: Account) -> None:
        """Add an account"""
        pass

    @abstractmethod
    def get(self, account_id: str) -> Optional[Account]:
        """Get account by ID"""
        pass

    @abstractmethod
    def list(self) -> List[Account]:
        """List all accounts"""
        pass

    @abstractmethod
    def update(self, account: Account) -> None:
        """Update an existing account"""
        pass


class AbstractMarketDataRepository(ABC):
    """
    Repository for market data retrieval.

    This repository is read-only and focuses on querying historical data
    from various sources (CSV, PostgreSQL, APIs).
    """

    @abstractmethod
    def get_bars(
        self,
        asset: Asset,
        resolution: BarResolution,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Bar]:
        """
        Retrieve historical bars for an asset.

        Args:
            asset: The asset to retrieve data for
            resolution: Time resolution (1M, 5M, 1H, 1D, etc.)
            start_date: Start of time range
            end_date: End of time range

        Returns:
            List of Bar objects sorted by timestamp
        """
        raise NotImplementedError

    @abstractmethod
    def get_ticks(
        self,
        asset: Asset,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Tick]:
        """
        Retrieve historical ticks for an asset.

        Args:
            asset: The asset to retrieve data for
            start_date: Start of time range
            end_date: End of time range

        Returns:
            List of Tick objects sorted by timestamp
        """
        raise NotImplementedError

    @abstractmethod
    def get_latest_bar(self, asset: Asset, resolution: BarResolution) -> Optional[Bar]:
        """Get the most recent bar for an asset"""
        raise NotImplementedError

    @abstractmethod
    def get_latest_price(self, asset: Asset) -> Optional[Decimal]:
        """Get the latest price for an asset"""
        raise NotImplementedError
