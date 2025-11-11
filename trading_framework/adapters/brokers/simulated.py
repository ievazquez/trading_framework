"""
Simulated Broker for Backtesting

Provides a simulated trading environment that mimics real broker behavior
without executing actual trades. Perfect for backtesting strategies.
"""

import asyncio
import logging
from typing import List, Optional, Dict, Callable
from datetime import datetime
from decimal import Decimal
import uuid

from .base import AbstractBroker, ConnectionStatus
from ...domain.model import (
    Order,
    OrderStatus,
    OrderSide,
    Position,
    Account,
    Asset,
    Bar,
    Tick,
)


logger = logging.getLogger(__name__)


class SimulatedBroker(AbstractBroker):
    """
    Simulated broker for backtesting.

    Executes orders against simulated market data without real trades.
    """

    def __init__(self, config: dict):
        super().__init__("SimulatedBroker", config)

        # Simulated state
        self._accounts: Dict[str, Account] = {}
        self._orders: Dict[str, Order] = {}
        self._positions: Dict[str, Position] = {}

        # Market data subscriptions
        self._bar_subscribers: Dict[str, List[Callable]] = {}
        self._tick_subscribers: Dict[str, List[Callable]] = {}

        # Current market prices
        self._current_prices: Dict[str, Decimal] = {}

        # Execution settings
        self.slippage_pct = Decimal(config.get("slippage_pct", "0.001"))  # 0.1% default
        self.commission_per_share = Decimal(config.get("commission_per_share", "0.01"))
        self.fill_immediately = config.get("fill_immediately", True)

    async def connect(self) -> bool:
        """Connect to simulated broker (always succeeds)"""
        logger.info("Connecting to simulated broker")
        self.connection.status = ConnectionStatus.CONNECTED
        self.connection.last_heartbeat = datetime.utcnow()
        return True

    async def disconnect(self) -> None:
        """Disconnect from simulated broker"""
        logger.info("Disconnecting from simulated broker")
        self.connection.status = ConnectionStatus.DISCONNECTED

    def is_connected(self) -> bool:
        """Check connection status"""
        return self.connection.is_connected()

    def add_account(self, account: Account) -> None:
        """Add an account to the simulated broker"""
        self._accounts[account.account_id] = account
        logger.info(f"Added account {account.account_id} with balance ${account.cash_balance}")

    async def get_account(self, account_id: str) -> Optional[Account]:
        """Get account information"""
        return self._accounts.get(account_id)

    async def get_positions(self, account_id: str) -> List[Position]:
        """Get all positions for an account"""
        account = self._accounts.get(account_id)
        if not account:
            return []
        return list(account.positions.values())

    async def get_position(
        self,
        account_id: str,
        asset: Asset
    ) -> Optional[Position]:
        """Get position for a specific asset"""
        account = self._accounts.get(account_id)
        if not account:
            return None
        return account.positions.get(asset.full_symbol)

    async def submit_order(self, order: Order) -> str:
        """
        Submit an order to the simulated broker.

        In immediate fill mode, orders are executed immediately at current price.
        Otherwise, they're queued and executed when price conditions are met.
        """
        logger.info(f"Submitting order: {order}")

        # Generate broker order ID
        broker_order_id = f"SIM_{uuid.uuid4().hex[:8]}"

        # Accept the order
        order.accept(broker_order_id)
        self._orders[order.order_id] = order

        # If immediate fill mode, execute now
        if self.fill_immediately:
            await self._execute_order(order)

        return broker_order_id

    async def _execute_order(self, order: Order) -> None:
        """Execute an order in the simulated environment"""
        # Get current price
        current_price = self._current_prices.get(order.asset.full_symbol)

        if current_price is None:
            logger.warning(f"No price available for {order.asset.symbol}, rejecting order")
            order.reject("No market price available")
            return

        # Apply slippage
        if order.side == OrderSide.BUY:
            fill_price = current_price * (1 + self.slippage_pct)
        else:
            fill_price = current_price * (1 - self.slippage_pct)

        # Round to asset's minimum price increment
        if order.asset.min_price_increment:
            fill_price = (fill_price // order.asset.min_price_increment) * order.asset.min_price_increment

        # Check limit price conditions
        if order.limit_price:
            if order.side == OrderSide.BUY and fill_price > order.limit_price:
                logger.debug(f"Order {order.order_id} not filled: price {fill_price} > limit {order.limit_price}")
                return
            elif order.side == OrderSide.SELL and fill_price < order.limit_price:
                logger.debug(f"Order {order.order_id} not filled: price {fill_price} < limit {order.limit_price}")
                return

        # Fill the order
        logger.info(f"Filling order {order.order_id} at price {fill_price}")
        order.fill(order.quantity, fill_price)

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        order = self._orders.get(order_id)
        if not order:
            logger.warning(f"Order {order_id} not found")
            return False

        if order.is_terminal:
            logger.warning(f"Cannot cancel order {order_id} in state {order.status}")
            return False

        order.cancel("Cancelled by user")
        logger.info(f"Cancelled order {order_id}")
        return True

    async def modify_order(
        self,
        order_id: str,
        quantity: Optional[Decimal] = None,
        limit_price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None
    ) -> bool:
        """Modify an existing order"""
        order = self._orders.get(order_id)
        if not order:
            logger.warning(f"Order {order_id} not found")
            return False

        if not order.is_active:
            logger.warning(f"Cannot modify order {order_id} in state {order.status}")
            return False

        # Modify order (simplified - would need to update the order object properly)
        logger.info(f"Modified order {order_id}")
        return True

    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order details"""
        return self._orders.get(order_id)

    async def get_orders(
        self,
        account_id: str,
        active_only: bool = False
    ) -> List[Order]:
        """Get orders for an account"""
        orders = list(self._orders.values())
        if active_only:
            orders = [o for o in orders if o.is_active]
        return orders

    async def get_latest_price(self, asset: Asset) -> Optional[Decimal]:
        """Get latest price for an asset"""
        return self._current_prices.get(asset.full_symbol)

    def update_price(self, asset: Asset, price: Decimal) -> None:
        """Update the current price for an asset (for backtesting)"""
        self._current_prices[asset.full_symbol] = price

        # Check if any pending orders can be filled
        for order in self._orders.values():
            if order.is_active and order.asset.full_symbol == asset.full_symbol:
                asyncio.create_task(self._execute_order(order))

    async def get_latest_bar(self, asset: Asset) -> Optional[Bar]:
        """Get latest bar (not implemented in simulated broker)"""
        return None

    async def subscribe_bars(
        self,
        asset: Asset,
        callback: Callable[[Bar], None]
    ) -> None:
        """Subscribe to real-time bars"""
        key = asset.full_symbol
        if key not in self._bar_subscribers:
            self._bar_subscribers[key] = []
        self._bar_subscribers[key].append(callback)
        logger.info(f"Subscribed to bars for {asset.symbol}")

    async def subscribe_ticks(
        self,
        asset: Asset,
        callback: Callable[[Tick], None]
    ) -> None:
        """Subscribe to real-time ticks"""
        key = asset.full_symbol
        if key not in self._tick_subscribers:
            self._tick_subscribers[key] = []
        self._tick_subscribers[key].append(callback)
        logger.info(f"Subscribed to ticks for {asset.symbol}")

    async def unsubscribe(self, asset: Asset) -> None:
        """Unsubscribe from market data"""
        key = asset.full_symbol
        if key in self._bar_subscribers:
            del self._bar_subscribers[key]
        if key in self._tick_subscribers:
            del self._tick_subscribers[key]
        logger.info(f"Unsubscribed from {asset.symbol}")

    def publish_bar(self, bar: Bar) -> None:
        """Publish a bar to subscribers (for backtesting)"""
        key = bar.asset.full_symbol

        # Update current price
        self.update_price(bar.asset, bar.close)

        # Notify subscribers
        callbacks = self._bar_subscribers.get(key, [])
        for callback in callbacks:
            try:
                callback(bar)
            except Exception as e:
                logger.error(f"Error in bar callback: {e}", exc_info=True)

    def publish_tick(self, tick: Tick) -> None:
        """Publish a tick to subscribers (for backtesting)"""
        key = tick.asset.full_symbol

        # Update current price
        if tick.price:
            self.update_price(tick.asset, tick.price)

        # Notify subscribers
        callbacks = self._tick_subscribers.get(key, [])
        for callback in callbacks:
            try:
                callback(tick)
            except Exception as e:
                logger.error(f"Error in tick callback: {e}", exc_info=True)

    async def search_assets(self, query: str) -> List[Asset]:
        """Search for assets (returns empty list in simulated broker)"""
        return []

    async def get_asset(self, symbol: str) -> Optional[Asset]:
        """Get asset details (returns None in simulated broker)"""
        return None
