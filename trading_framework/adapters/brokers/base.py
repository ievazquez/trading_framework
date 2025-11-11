"""
Base Broker Adapter Interface

Defines the common interface that all broker adapters must implement.
This abstraction allows the system to work with any broker without
changing the core business logic.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Callable
from datetime import datetime
from decimal import Decimal
from enum import Enum

from ...domain.model import Order, Position, Account, Asset, Bar, Tick


class ConnectionStatus(Enum):
    """Broker connection status"""
    DISCONNECTED = "DISCONNECTED"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    RECONNECTING = "RECONNECTING"
    ERROR = "ERROR"


class BrokerConnection:
    """Represents a connection to a broker"""

    def __init__(self, broker_name: str):
        self.broker_name = broker_name
        self.status = ConnectionStatus.DISCONNECTED
        self.last_heartbeat: Optional[datetime] = None
        self.error_message: Optional[str] = None

    def is_connected(self) -> bool:
        """Check if connection is active"""
        return self.status == ConnectionStatus.CONNECTED


class AbstractBroker(ABC):
    """
    Abstract base class for all broker adapters.

    Each broker adapter translates the generic trading operations
    into broker-specific API calls.
    """

    def __init__(self, broker_name: str, config: dict):
        self.broker_name = broker_name
        self.config = config
        self.connection = BrokerConnection(broker_name)

    # Connection Management

    @abstractmethod
    async def connect(self) -> bool:
        """
        Establish connection to the broker.

        Returns:
            True if connection successful, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the broker"""
        raise NotImplementedError

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to broker"""
        raise NotImplementedError

    # Account Operations

    @abstractmethod
    async def get_account(self, account_id: str) -> Optional[Account]:
        """
        Get account information.

        Args:
            account_id: Account identifier

        Returns:
            Account object or None if not found
        """
        raise NotImplementedError

    @abstractmethod
    async def get_positions(self, account_id: str) -> List[Position]:
        """
        Get all positions for an account.

        Args:
            account_id: Account identifier

        Returns:
            List of Position objects
        """
        raise NotImplementedError

    @abstractmethod
    async def get_position(
        self,
        account_id: str,
        asset: Asset
    ) -> Optional[Position]:
        """
        Get position for a specific asset.

        Args:
            account_id: Account identifier
            asset: Asset to get position for

        Returns:
            Position object or None if no position exists
        """
        raise NotImplementedError

    # Order Operations

    @abstractmethod
    async def submit_order(self, order: Order) -> str:
        """
        Submit an order to the broker.

        Args:
            order: Order to submit

        Returns:
            Broker's order ID

        Raises:
            Exception if order submission fails
        """
        raise NotImplementedError

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: ID of order to cancel

        Returns:
            True if cancellation successful
        """
        raise NotImplementedError

    @abstractmethod
    async def modify_order(
        self,
        order_id: str,
        quantity: Optional[Decimal] = None,
        limit_price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None
    ) -> bool:
        """
        Modify an existing order.

        Args:
            order_id: ID of order to modify
            quantity: New quantity (if changing)
            limit_price: New limit price (if changing)
            stop_price: New stop price (if changing)

        Returns:
            True if modification successful
        """
        raise NotImplementedError

    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get order details.

        Args:
            order_id: Order ID

        Returns:
            Order object or None if not found
        """
        raise NotImplementedError

    @abstractmethod
    async def get_orders(
        self,
        account_id: str,
        active_only: bool = False
    ) -> List[Order]:
        """
        Get orders for an account.

        Args:
            account_id: Account identifier
            active_only: If True, only return active orders

        Returns:
            List of Order objects
        """
        raise NotImplementedError

    # Market Data Operations

    @abstractmethod
    async def get_latest_price(self, asset: Asset) -> Optional[Decimal]:
        """
        Get latest price for an asset.

        Args:
            asset: Asset to get price for

        Returns:
            Latest price or None
        """
        raise NotImplementedError

    @abstractmethod
    async def get_latest_bar(self, asset: Asset) -> Optional[Bar]:
        """
        Get latest bar for an asset.

        Args:
            asset: Asset to get bar for

        Returns:
            Latest Bar or None
        """
        raise NotImplementedError

    @abstractmethod
    async def subscribe_bars(
        self,
        asset: Asset,
        callback: Callable[[Bar], None]
    ) -> None:
        """
        Subscribe to real-time bars.

        Args:
            asset: Asset to subscribe to
            callback: Function to call when new bar arrives
        """
        raise NotImplementedError

    @abstractmethod
    async def subscribe_ticks(
        self,
        asset: Asset,
        callback: Callable[[Tick], None]
    ) -> None:
        """
        Subscribe to real-time ticks.

        Args:
            asset: Asset to subscribe to
            callback: Function to call when new tick arrives
        """
        raise NotImplementedError

    @abstractmethod
    async def unsubscribe(self, asset: Asset) -> None:
        """
        Unsubscribe from market data for an asset.

        Args:
            asset: Asset to unsubscribe from
        """
        raise NotImplementedError

    # Asset/Symbol Operations

    @abstractmethod
    async def search_assets(self, query: str) -> List[Asset]:
        """
        Search for assets/symbols.

        Args:
            query: Search query

        Returns:
            List of matching Asset objects
        """
        raise NotImplementedError

    @abstractmethod
    async def get_asset(self, symbol: str) -> Optional[Asset]:
        """
        Get asset details by symbol.

        Args:
            symbol: Asset symbol

        Returns:
            Asset object or None
        """
        raise NotImplementedError

    # Utility Methods

    def normalize_symbol(self, symbol: str) -> str:
        """
        Normalize a symbol to broker's format.

        Different brokers use different symbol formats.
        Override this in subclasses if needed.
        """
        return symbol

    def denormalize_symbol(self, symbol: str) -> str:
        """
        Convert broker's symbol format to standard format.

        Override this in subclasses if needed.
        """
        return symbol
