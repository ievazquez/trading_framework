"""Asset domain model representing tradeable instruments"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional
from decimal import Decimal


class AssetType(Enum):
    """Types of tradeable assets"""
    FOREX = "FOREX"
    CRYPTO = "CRYPTO"
    STOCK = "STOCK"
    FUTURE = "FUTURE"
    INDEX = "INDEX"
    OPTION = "OPTION"
    CFD = "CFD"


@dataclass(frozen=True)
class Asset:
    """
    Represents a tradeable financial instrument.

    This is a Value Object - immutable and identified by its attributes.
    """
    symbol: str
    asset_type: AssetType
    exchange: str
    currency: str = "USD"

    # Contract specifications
    min_quantity: Optional[Decimal] = None
    max_quantity: Optional[Decimal] = None
    quantity_increment: Optional[Decimal] = None
    min_price_increment: Optional[Decimal] = None

    # For derivatives
    multiplier: Decimal = Decimal("1.0")
    expiration_date: Optional[str] = None
    strike_price: Optional[Decimal] = None

    # Metadata
    name: Optional[str] = None
    sector: Optional[str] = None

    def __post_init__(self):
        """Validate asset configuration"""
        if not self.symbol:
            raise ValueError("Asset symbol cannot be empty")
        if not self.exchange:
            raise ValueError("Asset exchange cannot be empty")

    @property
    def full_symbol(self) -> str:
        """Returns fully qualified symbol (symbol@exchange)"""
        return f"{self.symbol}@{self.exchange}"

    def __str__(self) -> str:
        return f"{self.symbol} ({self.asset_type.value})"

    def __repr__(self) -> str:
        return f"Asset(symbol='{self.symbol}', type={self.asset_type.value}, exchange='{self.exchange}')"
