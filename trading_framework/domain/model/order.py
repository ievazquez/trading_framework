"""Order domain model and related value objects"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
from decimal import Decimal
import uuid

from .asset import Asset
from ..events import Event


class OrderType(Enum):
    """Types of orders"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"
    MARKET_ON_CLOSE = "MARKET_ON_CLOSE"
    LIMIT_ON_CLOSE = "LIMIT_ON_CLOSE"


class OrderSide(Enum):
    """Order side"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Order lifecycle states"""
    PENDING = "PENDING"  # Created but not submitted
    SUBMITTED = "SUBMITTED"  # Submitted to broker
    ACCEPTED = "ACCEPTED"  # Accepted by broker
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TimeInForce(Enum):
    """Time in force specifications"""
    DAY = "DAY"  # Good for the day
    GTC = "GTC"  # Good till cancelled
    IOC = "IOC"  # Immediate or cancel
    FOK = "FOK"  # Fill or kill
    GTD = "GTD"  # Good till date
    OPG = "OPG"  # At the opening
    CLS = "CLS"  # At the close


@dataclass
class Order:
    """
    Represents a trading order (Aggregate Root).

    An Order is an aggregate that manages its own lifecycle and emits events
    when its state changes.
    """
    # Identity
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    client_order_id: Optional[str] = None
    broker_order_id: Optional[str] = None

    # Order details
    asset: Asset = None
    side: OrderSide = None
    order_type: OrderType = None
    quantity: Decimal = Decimal("0")

    # Pricing
    limit_price: Optional[Decimal] = None
    stop_price: Optional[Decimal] = None
    trailing_percent: Optional[Decimal] = None

    # Execution constraints
    time_in_force: TimeInForce = TimeInForce.GTC
    good_till_date: Optional[datetime] = None

    # Status tracking
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: Decimal = Decimal("0")
    average_fill_price: Optional[Decimal] = None

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    submitted_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None

    # Risk management
    parent_order_id: Optional[str] = None  # For OCO, bracket orders
    child_order_ids: List[str] = field(default_factory=list)

    # Metadata
    strategy_id: Optional[str] = None
    tags: dict = field(default_factory=dict)
    notes: Optional[str] = None

    # Events (not persisted)
    events: List[Event] = field(default_factory=list, repr=False)

    def __post_init__(self):
        """Validate order configuration"""
        if self.quantity <= 0:
            raise ValueError("Order quantity must be positive")
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("Limit orders require a limit price")
        if self.order_type in [OrderType.STOP, OrderType.STOP_LIMIT] and self.stop_price is None:
            raise ValueError("Stop orders require a stop price")

    @property
    def remaining_quantity(self) -> Decimal:
        """Returns unfilled quantity"""
        return self.quantity - self.filled_quantity

    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.filled_quantity >= self.quantity

    @property
    def is_active(self) -> bool:
        """Check if order is in an active state"""
        return self.status in [
            OrderStatus.SUBMITTED,
            OrderStatus.ACCEPTED,
            OrderStatus.PARTIALLY_FILLED
        ]

    @property
    def is_terminal(self) -> bool:
        """Check if order is in a terminal state"""
        return self.status in [
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
            OrderStatus.EXPIRED
        ]

    def submit(self) -> None:
        """Mark order as submitted"""
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot submit order in {self.status} state")

        self.status = OrderStatus.SUBMITTED
        self.submitted_at = datetime.utcnow()

        # Import here to avoid circular dependency
        from ..events import OrderSubmitted
        self.events.append(OrderSubmitted(
            order_id=self.order_id,
            asset=self.asset,
            side=self.side,
            quantity=self.quantity,
            order_type=self.order_type
        ))

    def accept(self, broker_order_id: str) -> None:
        """Mark order as accepted by broker"""
        if not self.is_active and self.status != OrderStatus.SUBMITTED:
            raise ValueError(f"Cannot accept order in {self.status} state")

        self.broker_order_id = broker_order_id
        self.status = OrderStatus.ACCEPTED

        from ..events import OrderAccepted
        self.events.append(OrderAccepted(
            order_id=self.order_id,
            broker_order_id=broker_order_id
        ))

    def fill(self, quantity: Decimal, price: Decimal, fill_time: datetime = None) -> None:
        """Record a fill (partial or complete)"""
        if not self.is_active:
            raise ValueError(f"Cannot fill order in {self.status} state")

        if quantity <= 0:
            raise ValueError("Fill quantity must be positive")

        if self.filled_quantity + quantity > self.quantity:
            raise ValueError("Fill quantity exceeds order quantity")

        # Update fill metrics
        total_filled = self.filled_quantity + quantity
        if self.average_fill_price is None:
            self.average_fill_price = price
        else:
            # Weighted average
            total_value = (self.average_fill_price * self.filled_quantity) + (price * quantity)
            self.average_fill_price = total_value / total_filled

        self.filled_quantity = total_filled
        fill_timestamp = fill_time or datetime.utcnow()

        # Update status
        if self.is_filled:
            self.status = OrderStatus.FILLED
            self.filled_at = fill_timestamp
        else:
            self.status = OrderStatus.PARTIALLY_FILLED

        from ..events import OrderFilled
        self.events.append(OrderFilled(
            order_id=self.order_id,
            asset=self.asset,
            side=self.side,
            quantity=quantity,
            price=price,
            filled_quantity=self.filled_quantity,
            is_complete=self.is_filled,
            timestamp=fill_timestamp
        ))

    def cancel(self, reason: Optional[str] = None) -> None:
        """Cancel the order"""
        if self.is_terminal:
            raise ValueError(f"Cannot cancel order in {self.status} state")

        self.status = OrderStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()

        from ..events import OrderCancelled
        self.events.append(OrderCancelled(
            order_id=self.order_id,
            reason=reason
        ))

    def reject(self, reason: str) -> None:
        """Mark order as rejected"""
        if self.status not in [OrderStatus.PENDING, OrderStatus.SUBMITTED]:
            raise ValueError(f"Cannot reject order in {self.status} state")

        self.status = OrderStatus.REJECTED

        from ..events import OrderRejected
        self.events.append(OrderRejected(
            order_id=self.order_id,
            reason=reason
        ))

    def __str__(self) -> str:
        return (f"Order({self.order_id[:8]}... {self.side.value} {self.quantity} "
                f"{self.asset.symbol} @ {self.order_type.value} - {self.status.value})")

    def __repr__(self) -> str:
        return self.__str__()
