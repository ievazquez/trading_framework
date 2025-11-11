"""Market data related events"""

from dataclasses import dataclass
from typing import Any

from .base import Event


@dataclass
class MarketDataReceived(Event):
    """Base event for market data"""
    asset: Any = None
    data: Any = None


@dataclass
class BarReceived(MarketDataReceived):
    """Event emitted when a new bar/candlestick is received"""
    bar: Any = None  # Bar object

    def __post_init__(self):
        if self.bar:
            object.__setattr__(self, 'asset', self.bar.asset)
            object.__setattr__(self, 'data', self.bar)
        super().__post_init__()


@dataclass
class TickReceived(MarketDataReceived):
    """Event emitted when a new tick is received"""
    tick: Any = None  # Tick object

    def __post_init__(self):
        if self.tick:
            object.__setattr__(self, 'asset', self.tick.asset)
            object.__setattr__(self, 'data', self.tick)
        super().__post_init__()
