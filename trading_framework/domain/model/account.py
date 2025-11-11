"""Account domain model for portfolio and balance tracking"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from .asset import Asset
from .position import Position
from ..events import Event


@dataclass
class Account:
    """
    Represents a trading account (Aggregate Root).

    Manages portfolio positions, cash balance, and risk metrics.
    """
    # Identity
    account_id: str
    broker: str
    account_number: Optional[str] = None

    # Balance tracking
    cash_balance: Decimal = Decimal("0")
    initial_balance: Decimal = Decimal("0")

    # Positions
    positions: Dict[str, Position] = field(default_factory=dict)  # asset.full_symbol -> Position

    # Risk metrics
    buying_power: Decimal = Decimal("0")
    margin_used: Decimal = Decimal("0")
    maintenance_margin: Decimal = Decimal("0")

    # Performance tracking
    total_realized_pnl: Decimal = Decimal("0")
    total_unrealized_pnl: Decimal = Decimal("0")
    total_commission: Decimal = Decimal("0")
    total_fees: Decimal = Decimal("0")

    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    # Metadata
    currency: str = "USD"
    tags: dict = field(default_factory=dict)

    # Events
    events: List[Event] = field(default_factory=list, repr=False)

    @property
    def total_equity(self) -> Decimal:
        """Total account equity (cash + positions value)"""
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash_balance + positions_value

    @property
    def total_pnl(self) -> Decimal:
        """Total P&L (realized + unrealized)"""
        return self.total_realized_pnl + self.total_unrealized_pnl

    @property
    def net_liquidation_value(self) -> Decimal:
        """Net liquidation value"""
        return self.total_equity

    @property
    def available_cash(self) -> Decimal:
        """Cash available for trading"""
        return min(self.cash_balance, self.buying_power)

    @property
    def leverage(self) -> Decimal:
        """Current leverage ratio"""
        if self.total_equity == 0:
            return Decimal("0")
        positions_value = sum(pos.market_value for pos in self.positions.values())
        return positions_value / self.total_equity if self.total_equity > 0 else Decimal("0")

    def get_position(self, asset: Asset) -> Optional[Position]:
        """Get position for an asset"""
        return self.positions.get(asset.full_symbol)

    def update_cash(self, amount: Decimal, reason: str = None) -> None:
        """Update cash balance"""
        self.cash_balance += amount
        self.last_updated = datetime.utcnow()

        from ..events import AccountBalanceUpdated
        self.events.append(AccountBalanceUpdated(
            account_id=self.account_id,
            cash_balance=self.cash_balance,
            total_equity=self.total_equity,
            reason=reason
        ))

    def update_position(self, position: Position) -> None:
        """Update or add a position"""
        self.positions[position.asset.full_symbol] = position

        # Recalculate unrealized P&L
        self.total_unrealized_pnl = sum(
            pos.unrealized_pnl for pos in self.positions.values()
        )
        self.last_updated = datetime.utcnow()

    def remove_position(self, asset: Asset) -> None:
        """Remove a closed position"""
        if asset.full_symbol in self.positions:
            del self.positions[asset.full_symbol]
            self.last_updated = datetime.utcnow()

    def update_prices(self, prices: Dict[str, Decimal]) -> None:
        """
        Update prices for all positions.

        Args:
            prices: Dict mapping asset.full_symbol to current price
        """
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.update_price(prices[symbol])

        # Recalculate total unrealized P&L
        self.total_unrealized_pnl = sum(
            pos.unrealized_pnl for pos in self.positions.values()
        )
        self.last_updated = datetime.utcnow()

    def calculate_risk_metrics(self) -> dict:
        """Calculate comprehensive risk metrics"""
        return {
            "total_equity": float(self.total_equity),
            "cash_balance": float(self.cash_balance),
            "buying_power": float(self.buying_power),
            "leverage": float(self.leverage),
            "margin_used": float(self.margin_used),
            "maintenance_margin": float(self.maintenance_margin),
            "total_pnl": float(self.total_pnl),
            "realized_pnl": float(self.total_realized_pnl),
            "unrealized_pnl": float(self.total_unrealized_pnl),
            "return_pct": float((self.total_equity - self.initial_balance) / self.initial_balance * 100)
            if self.initial_balance > 0 else 0.0,
            "num_positions": len(self.positions),
            "positions_value": float(sum(pos.market_value for pos in self.positions.values())),
        }

    def __str__(self) -> str:
        return (f"Account({self.account_id} | Equity: ${self.total_equity:,.2f} | "
                f"Positions: {len(self.positions)} | P&L: ${self.total_pnl:,.2f})")
