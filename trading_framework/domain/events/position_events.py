"""Position-related domain events"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from .base import DomainEvent


@dataclass
class PositionUpdated(DomainEvent):
    """Event emitted when a position is updated"""
    position_id: str = None
    asset: Any = None
    quantity: Decimal = None
    current_price: Decimal = None
    unrealized_pnl: Decimal = None
    total_pnl: Decimal = None

    def __post_init__(self):
        if not self.aggregate_id:
            object.__setattr__(self, 'aggregate_id', self.position_id)
        super().__post_init__()


@dataclass
class PositionReduced(DomainEvent):
    """Event emitted when a position size is reduced"""
    position_id: str = None
    asset: Any = None
    quantity_reduced: Decimal = None
    price: Decimal = None
    realized_pnl: Decimal = None
    remaining_quantity: Decimal = None

    def __post_init__(self):
        if not self.aggregate_id:
            object.__setattr__(self, 'aggregate_id', self.position_id)
        super().__post_init__()


@dataclass
class PositionClosed(DomainEvent):
    """Event emitted when a position is closed"""
    position_id: str = None
    asset: Any = None
    close_price: Decimal = None
    realized_pnl: Decimal = None
    total_pnl: Decimal = None

    def __post_init__(self):
        if not self.aggregate_id:
            object.__setattr__(self, 'aggregate_id', self.position_id)
        super().__post_init__()
