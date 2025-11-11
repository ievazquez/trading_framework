"""Bar (candlestick) domain model for OHLCV data"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from .asset import Asset


class BarResolution(Enum):
    """Time resolution for bars"""
    TICK = "TICK"
    SEC_1 = "1S"
    SEC_5 = "5S"
    SEC_10 = "10S"
    SEC_15 = "15S"
    SEC_30 = "30S"
    MIN_1 = "1M"
    MIN_5 = "5M"
    MIN_15 = "15M"
    MIN_30 = "30M"
    HOUR_1 = "1H"
    HOUR_4 = "4H"
    DAY_1 = "1D"
    WEEK_1 = "1W"
    MONTH_1 = "1MO"


@dataclass(frozen=True)
class Bar:
    """
    Represents a price bar/candlestick (Value Object).

    Contains OHLCV data for a specific time period.
    """
    # Identity
    asset: Asset
    timestamp: datetime
    resolution: BarResolution

    # OHLCV data
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal = Decimal("0")

    # Additional data
    vwap: Optional[Decimal] = None  # Volume-weighted average price
    trades_count: Optional[int] = None
    bid: Optional[Decimal] = None
    ask: Optional[Decimal] = None
    spread: Optional[Decimal] = None

    def __post_init__(self):
        """Validate bar data"""
        if self.high < self.low:
            raise ValueError("High must be >= Low")
        if self.high < self.open or self.high < self.close:
            raise ValueError("High must be >= Open and Close")
        if self.low > self.open or self.low > self.close:
            raise ValueError("Low must be <= Open and Close")
        if self.volume < 0:
            raise ValueError("Volume cannot be negative")

    @property
    def range(self) -> Decimal:
        """Price range (high - low)"""
        return self.high - self.low

    @property
    def body(self) -> Decimal:
        """Candle body size (|close - open|)"""
        return abs(self.close - self.open)

    @property
    def upper_wick(self) -> Decimal:
        """Upper wick/shadow size"""
        return self.high - max(self.open, self.close)

    @property
    def lower_wick(self) -> Decimal:
        """Lower wick/shadow size"""
        return min(self.open, self.close) - self.low

    @property
    def is_bullish(self) -> bool:
        """Check if bar is bullish (close > open)"""
        return self.close > self.open

    @property
    def is_bearish(self) -> bool:
        """Check if bar is bearish (close < open)"""
        return self.close < self.open

    @property
    def is_doji(self) -> bool:
        """Check if bar is a doji (close ~= open)"""
        return self.body / self.range < Decimal("0.1") if self.range > 0 else True

    @property
    def typical_price(self) -> Decimal:
        """Typical price (HLC/3)"""
        return (self.high + self.low + self.close) / Decimal("3")

    def __str__(self) -> str:
        return (f"Bar({self.asset.symbol} {self.resolution.value} {self.timestamp} "
                f"O:{self.open} H:{self.high} L:{self.low} C:{self.close} V:{self.volume})")

    def __repr__(self) -> str:
        return self.__str__()
