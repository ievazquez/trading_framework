"""Order-related domain events"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from .base import DomainEvent


@dataclass
class OrderSubmitted(DomainEvent):
    """Event emitted when an order is submitted to the broker"""
    order_id: str = None
    asset: Any = None
    side: Any = None
    quantity: Decimal = None
    order_type: Any = None

    def __post_init__(self):
        if not self.aggregate_id:
            object.__setattr__(self, 'aggregate_id', self.order_id)
        super().__post_init__()


@dataclass
class OrderAccepted(DomainEvent):
    """Event emitted when an order is accepted by the broker"""
    order_id: str = None
    broker_order_id: str = None

    def __post_init__(self):
        if not self.aggregate_id:
            object.__setattr__(self, 'aggregate_id', self.order_id)
        super().__post_init__()


@dataclass
class OrderFilled(DomainEvent):
    """Event emitted when an order is filled (partially or completely)"""
    order_id: str = None
    asset: Any = None
    side: Any = None
    quantity: Decimal = None
    price: Decimal = None
    filled_quantity: Decimal = None
    is_complete: bool = False
    fill_timestamp: datetime = None

    def __post_init__(self):
        if not self.aggregate_id:
            object.__setattr__(self, 'aggregate_id', self.order_id)
        super().__post_init__()


@dataclass
class OrderCancelled(DomainEvent):
    """Event emitted when an order is cancelled"""
    order_id: str = None
    reason: Optional[str] = None

    def __post_init__(self):
        if not self.aggregate_id:
            object.__setattr__(self, 'aggregate_id', self.order_id)
        super().__post_init__()


@dataclass
class OrderRejected(DomainEvent):
    """Event emitted when an order is rejected by the broker"""
    order_id: str = None
    reason: str = None

    def __post_init__(self):
        if not self.aggregate_id:
            object.__setattr__(self, 'aggregate_id', self.order_id)
        super().__post_init__()


# Import at module level to avoid issues
from typing import Any
