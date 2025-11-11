"""
Simple Moving Average Crossover Strategy

A classic trend-following strategy that buys when a fast SMA crosses above
a slow SMA and sells when it crosses below.

Strategy Rules:
- Buy signal: Fast SMA crosses above Slow SMA
- Sell signal: Fast SMA crosses below Slow SMA
- Position size: Fixed percentage of portfolio
"""

from decimal import Decimal
from typing import Optional, List
from collections import deque

from trading_framework.domain.model import (
    Order,
    OrderType,
    OrderSide,
    Asset,
    Bar,
)


class SimpleSMACrossover:
    """
    Simple Moving Average Crossover Strategy.

    Parameters:
        fast_period: Period for fast SMA (default: 10)
        slow_period: Period for slow SMA (default: 30)
        position_size_pct: Percentage of portfolio to allocate (default: 0.5 = 50%)
    """

    def __init__(
        self,
        fast_period: int = 10,
        slow_period: int = 30,
        position_size_pct: float = 0.5
    ):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.position_size_pct = Decimal(str(position_size_pct))

        # Price history for each asset
        self.price_history = {}  # asset.full_symbol -> deque of prices

        # Track previous SMA values for crossover detection
        self.prev_fast_sma = {}
        self.prev_slow_sma = {}

    def __call__(self, context: dict) -> Optional[List[Order]]:
        """
        Strategy entry point called on each bar.

        Args:
            context: Dictionary containing:
                - bar: Current bar
                - account: Account object
                - broker: Broker object
                - uow: Unit of Work

        Returns:
            List of orders to submit, or None
        """
        bar: Bar = context["bar"]
        account = context["account"]
        broker = context["broker"]

        # Initialize price history for this asset
        symbol = bar.asset.full_symbol
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.slow_period)

        # Add current price
        self.price_history[symbol].append(bar.close)

        # Need enough data to calculate SMAs
        if len(self.price_history[symbol]) < self.slow_period:
            return None

        # Calculate SMAs
        fast_sma = self._calculate_sma(symbol, self.fast_period)
        slow_sma = self._calculate_sma(symbol, self.slow_period)

        # Get previous SMA values
        prev_fast = self.prev_fast_sma.get(symbol)
        prev_slow = self.prev_slow_sma.get(symbol)

        # Store current SMAs for next iteration
        self.prev_fast_sma[symbol] = fast_sma
        self.prev_slow_sma[symbol] = slow_sma

        # Need previous values to detect crossover
        if prev_fast is None or prev_slow is None:
            return None

        # Check for crossover signals
        orders = []

        # Bullish crossover: Fast SMA crosses above Slow SMA
        if prev_fast <= prev_slow and fast_sma > slow_sma:
            print(f"[{bar.timestamp}] BUY SIGNAL: Fast SMA ({fast_sma:.2f}) "
                  f"crossed above Slow SMA ({slow_sma:.2f})")

            # Check if we already have a position
            position = account.get_position(bar.asset)
            if position and position.is_long:
                return None  # Already long

            # Calculate position size
            quantity = self._calculate_position_size(bar.asset, bar.close, account)

            if quantity > 0:
                order = Order(
                    asset=bar.asset,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=quantity,
                )
                orders.append(order)

        # Bearish crossover: Fast SMA crosses below Slow SMA
        elif prev_fast >= prev_slow and fast_sma < slow_sma:
            print(f"[{bar.timestamp}] SELL SIGNAL: Fast SMA ({fast_sma:.2f}) "
                  f"crossed below Slow SMA ({slow_sma:.2f})")

            # Check if we have a position to close
            position = account.get_position(bar.asset)
            if position and position.is_long:
                order = Order(
                    asset=bar.asset,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=position.quantity,
                )
                orders.append(order)

        return orders if orders else None

    def _calculate_sma(self, symbol: str, period: int) -> Decimal:
        """Calculate Simple Moving Average"""
        prices = list(self.price_history[symbol])[-period:]
        return sum(prices) / len(prices)

    def _calculate_position_size(
        self,
        asset: Asset,
        price: Decimal,
        account
    ) -> Decimal:
        """
        Calculate position size based on available capital.

        Uses fixed percentage of portfolio value.
        """
        # Calculate target position value
        target_value = account.total_equity * self.position_size_pct

        # Calculate quantity
        quantity = target_value / (price * asset.multiplier)

        # Round to asset's quantity increment
        if asset.quantity_increment:
            quantity = (quantity // asset.quantity_increment) * asset.quantity_increment

        # Respect min/max quantity limits
        if asset.min_quantity and quantity < asset.min_quantity:
            return Decimal("0")
        if asset.max_quantity and quantity > asset.max_quantity:
            quantity = asset.max_quantity

        return quantity
