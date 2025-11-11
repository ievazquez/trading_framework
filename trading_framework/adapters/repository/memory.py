"""In-memory repository implementations for testing and backtesting"""

from datetime import datetime
from typing import List, Optional, Dict
from decimal import Decimal

from .base import (
    AbstractOrderRepository,
    AbstractPositionRepository,
    AbstractAccountRepository,
    AbstractMarketDataRepository,
)
from ...domain.model import (
    Asset,
    Order,
    Position,
    Account,
    Bar,
    Tick,
    BarResolution,
    OrderStatus,
)


class InMemoryOrderRepository(AbstractOrderRepository):
    """In-memory implementation of order repository"""

    def __init__(self):
        self._orders: Dict[str, Order] = {}
        self._broker_id_index: Dict[str, str] = {}  # broker_order_id -> order_id

    def add(self, order: Order) -> None:
        self._orders[order.order_id] = order
        if order.broker_order_id:
            self._broker_id_index[order.broker_order_id] = order.order_id

    def get(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)

    def get_by_broker_id(self, broker_order_id: str) -> Optional[Order]:
        order_id = self._broker_id_index.get(broker_order_id)
        if order_id:
            return self._orders.get(order_id)
        return None

    def list(self, account_id: Optional[str] = None) -> List[Order]:
        orders = list(self._orders.values())
        if account_id:
            # Filter by account_id if we add that field to Order
            pass
        return orders

    def list_active(self, account_id: Optional[str] = None) -> List[Order]:
        active_orders = [o for o in self._orders.values() if o.is_active]
        return active_orders

    def update(self, order: Order) -> None:
        self._orders[order.order_id] = order
        if order.broker_order_id:
            self._broker_id_index[order.broker_order_id] = order.order_id


class InMemoryPositionRepository(AbstractPositionRepository):
    """In-memory implementation of position repository"""

    def __init__(self):
        self._positions: Dict[str, Position] = {}
        # Index by account_id and asset
        self._account_asset_index: Dict[tuple, str] = {}  # (account_id, asset.full_symbol) -> position_id

    def add(self, position: Position) -> None:
        self._positions[position.position_id] = position

    def get(self, position_id: str) -> Optional[Position]:
        return self._positions.get(position_id)

    def get_by_asset(self, account_id: str, asset: Asset) -> Optional[Position]:
        position_id = self._account_asset_index.get((account_id, asset.full_symbol))
        if position_id:
            return self._positions.get(position_id)
        return None

    def list(self, account_id: Optional[str] = None) -> List[Position]:
        return list(self._positions.values())

    def list_open(self, account_id: Optional[str] = None) -> List[Position]:
        return [p for p in self._positions.values() if p.is_open]

    def update(self, position: Position) -> None:
        self._positions[position.position_id] = position


class InMemoryAccountRepository(AbstractAccountRepository):
    """In-memory implementation of account repository"""

    def __init__(self):
        self._accounts: Dict[str, Account] = {}

    def add(self, account: Account) -> None:
        self._accounts[account.account_id] = account

    def get(self, account_id: str) -> Optional[Account]:
        return self._accounts.get(account_id)

    def list(self) -> List[Account]:
        return list(self._accounts.values())

    def update(self, account: Account) -> None:
        self._accounts[account.account_id] = account


class InMemoryMarketDataRepository(AbstractMarketDataRepository):
    """
    In-memory implementation of market data repository.

    Stores bars and ticks in memory for backtesting.
    """

    def __init__(self):
        # Bars indexed by: (asset.full_symbol, resolution) -> List[Bar]
        self._bars: Dict[tuple, List[Bar]] = {}

        # Ticks indexed by: asset.full_symbol -> List[Tick]
        self._ticks: Dict[str, List[Tick]] = {}

    def add_bars(self, bars: List[Bar]) -> None:
        """Add bars to the repository"""
        for bar in bars:
            key = (bar.asset.full_symbol, bar.resolution.value)
            if key not in self._bars:
                self._bars[key] = []
            self._bars[key].append(bar)

        # Sort by timestamp
        for key in self._bars:
            self._bars[key].sort(key=lambda b: b.timestamp)

    def add_ticks(self, ticks: List[Tick]) -> None:
        """Add ticks to the repository"""
        for tick in ticks:
            key = tick.asset.full_symbol
            if key not in self._ticks:
                self._ticks[key] = []
            self._ticks[key].append(tick)

        # Sort by timestamp
        for key in self._ticks:
            self._ticks[key].sort(key=lambda t: t.timestamp)

    def get_bars(
        self,
        asset: Asset,
        resolution: BarResolution,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Bar]:
        key = (asset.full_symbol, resolution.value)
        bars = self._bars.get(key, [])

        # Filter by date range
        filtered = [
            bar for bar in bars
            if start_date <= bar.timestamp <= end_date
        ]
        return filtered

    def get_ticks(
        self,
        asset: Asset,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Tick]:
        key = asset.full_symbol
        ticks = self._ticks.get(key, [])

        # Filter by date range
        filtered = [
            tick for tick in ticks
            if start_date <= tick.timestamp <= end_date
        ]
        return filtered

    def get_latest_bar(self, asset: Asset, resolution: BarResolution) -> Optional[Bar]:
        key = (asset.full_symbol, resolution.value)
        bars = self._bars.get(key, [])
        return bars[-1] if bars else None

    def get_latest_price(self, asset: Asset) -> Optional[Decimal]:
        # Try to get from latest bar
        for resolution in [BarResolution.MIN_1, BarResolution.MIN_5, BarResolution.DAY_1]:
            bar = self.get_latest_bar(asset, resolution)
            if bar:
                return bar.close

        # Try to get from latest tick
        key = asset.full_symbol
        ticks = self._ticks.get(key, [])
        if ticks:
            latest_tick = ticks[-1]
            return latest_tick.price or latest_tick.mid_price

        return None
