"""Position domain model"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from .asset import Asset
from ..events import Event


@dataclass
class Position:
    """
    Represents a trading position (Aggregate Root).

    A position tracks the current holdings of an asset, including realized
    and unrealized P&L.
    """
    # Identity
    position_id: str
    asset: Asset

    # Position details
    quantity: Decimal = Decimal("0")  # Positive = long, Negative = short
    average_entry_price: Decimal = Decimal("0")
    current_price: Decimal = Decimal("0")

    # P&L tracking
    realized_pnl: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    total_pnl: Decimal = Decimal("0")

    # Cost basis
    total_cost: Decimal = Decimal("0")

    # Timestamps
    opened_at: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)
    closed_at: Optional[datetime] = None

    # Metadata
    strategy_id: Optional[str] = None
    tags: dict = field(default_factory=dict)

    # Events
    events: List[Event] = field(default_factory=list, repr=False)

    @property
    def is_open(self) -> bool:
        """Check if position is open"""
        return self.quantity != 0

    @property
    def is_long(self) -> bool:
        """Check if position is long"""
        return self.quantity > 0

    @property
    def is_short(self) -> bool:
        """Check if position is short"""
        return self.quantity < 0

    @property
    def market_value(self) -> Decimal:
        """Current market value of position"""
        return abs(self.quantity) * self.current_price * self.asset.multiplier

    @property
    def cost_basis(self) -> Decimal:
        """Cost basis of position"""
        return abs(self.quantity) * self.average_entry_price * self.asset.multiplier

    def update_price(self, new_price: Decimal) -> None:
        """Update current price and recalculate unrealized P&L"""
        if new_price <= 0:
            raise ValueError("Price must be positive")

        self.current_price = new_price
        self.last_updated = datetime.utcnow()

        # Calculate unrealized P&L
        if self.is_long:
            self.unrealized_pnl = (new_price - self.average_entry_price) * self.quantity * self.asset.multiplier
        elif self.is_short:
            self.unrealized_pnl = (self.average_entry_price - new_price) * abs(self.quantity) * self.asset.multiplier
        else:
            self.unrealized_pnl = Decimal("0")

        self.total_pnl = self.realized_pnl + self.unrealized_pnl

        from ..events import PositionUpdated
        self.events.append(PositionUpdated(
            position_id=self.position_id,
            asset=self.asset,
            quantity=self.quantity,
            current_price=new_price,
            unrealized_pnl=self.unrealized_pnl,
            total_pnl=self.total_pnl
        ))

    def increase_position(self, quantity: Decimal, price: Decimal) -> None:
        """Increase position size (buy for long, sell for short)"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if not self.is_open:
            # Opening new position
            self.quantity = quantity
            self.average_entry_price = price
            self.total_cost = quantity * price * self.asset.multiplier
            self.opened_at = datetime.utcnow()
        else:
            # Adding to existing position
            if (self.is_long and quantity > 0) or (self.is_short and quantity < 0):
                # Same direction - update average entry price
                total_quantity = abs(self.quantity) + abs(quantity)
                total_cost = (abs(self.quantity) * self.average_entry_price +
                            abs(quantity) * price)
                self.average_entry_price = total_cost / total_quantity
                self.quantity += quantity
                self.total_cost += abs(quantity) * price * self.asset.multiplier

        self.current_price = price
        self.last_updated = datetime.utcnow()
        self.update_price(price)

    def reduce_position(self, quantity: Decimal, price: Decimal) -> None:
        """
        Reduce position size (sell for long, buy for short).
        Realizes P&L on the reduced portion.
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        if not self.is_open:
            raise ValueError("Cannot reduce closed position")

        if abs(quantity) > abs(self.quantity):
            raise ValueError("Reduction quantity exceeds position size")

        # Calculate realized P&L on the portion being closed
        if self.is_long:
            realized = (price - self.average_entry_price) * quantity * self.asset.multiplier
        else:
            realized = (self.average_entry_price - price) * quantity * self.asset.multiplier

        self.realized_pnl += realized
        self.quantity -= quantity if self.is_long else -quantity

        # Check if position is now closed
        if self.quantity == 0:
            self.closed_at = datetime.utcnow()
            self.unrealized_pnl = Decimal("0")

        self.current_price = price
        self.last_updated = datetime.utcnow()
        self.total_pnl = self.realized_pnl + self.unrealized_pnl

        from ..events import PositionReduced
        self.events.append(PositionReduced(
            position_id=self.position_id,
            asset=self.asset,
            quantity_reduced=quantity,
            price=price,
            realized_pnl=realized,
            remaining_quantity=self.quantity
        ))

    def close_position(self, price: Decimal) -> None:
        """Close entire position"""
        if not self.is_open:
            raise ValueError("Position already closed")

        self.reduce_position(abs(self.quantity), price)

        from ..events import PositionClosed
        self.events.append(PositionClosed(
            position_id=self.position_id,
            asset=self.asset,
            close_price=price,
            realized_pnl=self.realized_pnl,
            total_pnl=self.total_pnl
        ))

    def __str__(self) -> str:
        direction = "LONG" if self.is_long else "SHORT" if self.is_short else "FLAT"
        return (f"Position({self.asset.symbol} {direction} {abs(self.quantity)} @ "
                f"{self.average_entry_price} | P&L: {self.total_pnl:.2f})")
