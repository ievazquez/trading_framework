"""Tick domain model for granular market data"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from .asset import Asset


class TickType(Enum):
    """Type of tick data"""
    TRADE = "TRADE"
    BID = "BID"
    ASK = "ASK"
    QUOTE = "QUOTE"  # Both bid and ask


@dataclass(frozen=True)
class Tick:
    """
    Represents a market tick (Value Object).

    Contains the most granular level of market data.
    """
    # Identity
    asset: Asset
    timestamp: datetime
    tick_type: TickType

    # Price data
    price: Optional[Decimal] = None
    size: Optional[Decimal] = None

    # Bid/Ask data
    bid_price: Optional[Decimal] = None
    bid_size: Optional[Decimal] = None
    ask_price: Optional[Decimal] = None
    ask_size: Optional[Decimal] = None

    # Exchange/venue
    exchange: Optional[str] = None
    conditions: Optional[str] = None  # Trade conditions/flags

    # Sequence number for ordering
    sequence: Optional[int] = None

    @property
    def mid_price(self) -> Optional[Decimal]:
        """Calculate mid price from bid/ask"""
        if self.bid_price is not None and self.ask_price is not None:
            return (self.bid_price + self.ask_price) / Decimal("2")
        return None

    @property
    def spread(self) -> Optional[Decimal]:
        """Calculate bid-ask spread"""
        if self.bid_price is not None and self.ask_price is not None:
            return self.ask_price - self.bid_price
        return None

    @property
    def spread_bps(self) -> Optional[Decimal]:
        """Calculate spread in basis points"""
        if self.spread is not None and self.mid_price is not None and self.mid_price > 0:
            return (self.spread / self.mid_price) * Decimal("10000")
        return None

    def __str__(self) -> str:
        if self.tick_type == TickType.TRADE:
            return f"Tick({self.asset.symbol} TRADE {self.price} x {self.size} @ {self.timestamp})"
        elif self.tick_type == TickType.QUOTE:
            return (f"Tick({self.asset.symbol} QUOTE {self.bid_price}/{self.ask_price} "
                   f"@ {self.timestamp})")
        else:
            return f"Tick({self.asset.symbol} {self.tick_type.value} @ {self.timestamp})"

    def __repr__(self) -> str:
        return self.__str__()
