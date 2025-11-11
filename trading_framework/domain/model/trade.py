"""Trade domain model representing executed trades"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from .asset import Asset
from .order import OrderSide


class TradeStatus(Enum):
    """Trade execution status"""
    EXECUTED = "EXECUTED"
    SETTLED = "SETTLED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class Trade:
    """
    Represents an executed trade (Value Object).

    A Trade is immutable and represents a completed transaction.
    """
    # Identity
    trade_id: str
    order_id: str
    broker_trade_id: Optional[str] = None

    # Trade details
    asset: Asset = None
    side: OrderSide = None
    quantity: Decimal = Decimal("0")
    price: Decimal = Decimal("0")

    # Execution details
    executed_at: datetime = None
    settlement_date: Optional[datetime] = None

    # Costs
    commission: Decimal = Decimal("0")
    fees: Decimal = Decimal("0")
    slippage: Decimal = Decimal("0")

    # Status
    status: TradeStatus = TradeStatus.EXECUTED

    # Metadata
    strategy_id: Optional[str] = None
    venue: Optional[str] = None  # Execution venue
    liquidity_flag: Optional[str] = None  # Maker/Taker

    @property
    def gross_value(self) -> Decimal:
        """Gross trade value before costs"""
        return self.quantity * self.price

    @property
    def total_cost(self) -> Decimal:
        """Total transaction costs"""
        return self.commission + self.fees

    @property
    def net_value(self) -> Decimal:
        """Net trade value after costs"""
        if self.side == OrderSide.BUY:
            return self.gross_value + self.total_cost
        else:  # SELL
            return self.gross_value - self.total_cost

    def __str__(self) -> str:
        return (f"Trade({self.trade_id[:8]}... {self.side.value} {self.quantity} "
                f"{self.asset.symbol} @ {self.price})")
