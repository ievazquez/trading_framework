"""
Risk Manager

Centralized risk management component that validates orders and positions
against configured risk parameters before execution.

Features:
- Position size limits
- Leverage limits
- Maximum open positions
- Daily loss limits (circuit breaker)
- Portfolio heat (total risk exposure)
- Individual position risk
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List, Dict
from enum import Enum

from ..domain.model import Order, Account, Position, Asset, OrderSide


logger = logging.getLogger(__name__)


class RiskViolationType(Enum):
    """Types of risk violations"""
    POSITION_SIZE_EXCEEDED = "POSITION_SIZE_EXCEEDED"
    LEVERAGE_EXCEEDED = "LEVERAGE_EXCEEDED"
    MAX_POSITIONS_EXCEEDED = "MAX_POSITIONS_EXCEEDED"
    INSUFFICIENT_CAPITAL = "INSUFFICIENT_CAPITAL"
    DAILY_LOSS_LIMIT_EXCEEDED = "DAILY_LOSS_LIMIT_EXCEEDED"
    PORTFOLIO_HEAT_EXCEEDED = "PORTFOLIO_HEAT_EXCEEDED"
    POSITION_CONCENTRATION_EXCEEDED = "POSITION_CONCENTRATION_EXCEEDED"
    MIN_EQUITY_BREACHED = "MIN_EQUITY_BREACHED"


@dataclass
class RiskViolation:
    """Represents a risk rule violation"""
    violation_type: RiskViolationType
    message: str
    current_value: Optional[Decimal] = None
    limit_value: Optional[Decimal] = None
    severity: str = "ERROR"  # ERROR, WARNING


@dataclass
class RiskConfig:
    """Configuration for risk management"""

    # Position sizing
    max_position_size_pct: Decimal = Decimal("0.1")  # 10% of portfolio
    max_position_value: Optional[Decimal] = None  # Absolute limit

    # Leverage
    max_leverage: Decimal = Decimal("1.0")  # No leverage by default

    # Portfolio limits
    max_open_positions: int = 10
    max_positions_per_asset: int = 1

    # Circuit breakers
    max_daily_loss_pct: Decimal = Decimal("0.05")  # 5% daily loss
    max_daily_loss_absolute: Optional[Decimal] = None

    # Capital requirements
    min_equity: Optional[Decimal] = None
    reserve_capital_pct: Decimal = Decimal("0.1")  # Keep 10% in reserve

    # Concentration limits
    max_sector_concentration_pct: Decimal = Decimal("0.3")  # 30% per sector
    max_asset_type_concentration_pct: Decimal = Decimal("0.5")  # 50% per asset type

    # Portfolio heat (total risk)
    max_portfolio_heat_pct: Decimal = Decimal("0.2")  # 20% of portfolio at risk

    # Risk per trade
    max_risk_per_trade_pct: Decimal = Decimal("0.02")  # 2% per trade

    # Validation flags
    enforce_position_limits: bool = True
    enforce_leverage_limits: bool = True
    enforce_daily_loss_limits: bool = True
    enforce_concentration_limits: bool = True
    allow_warnings: bool = True  # Allow warnings without rejection


class RiskManager:
    """
    Centralized risk management.

    Validates all trading decisions against risk parameters.
    """

    def __init__(self, config: RiskConfig):
        """
        Initialize risk manager.

        Args:
            config: Risk configuration
        """
        self.config = config

        # Track daily P&L for circuit breaker
        self._daily_pnl: Dict[str, Decimal] = {}  # date -> pnl
        self._daily_start_equity: Dict[str, Decimal] = {}  # date -> starting equity

        # Track violations for reporting
        self.violation_history: List[RiskViolation] = []

        logger.info(f"RiskManager initialized with config: {config}")

    def validate_order(
        self,
        order: Order,
        account: Account
    ) -> tuple[bool, List[RiskViolation]]:
        """
        Validate an order against all risk rules.

        Args:
            order: Order to validate
            account: Current account state

        Returns:
            (is_valid, violations) - True if order passes all checks
        """
        violations = []

        # Run all validation checks
        violations.extend(self._check_capital_requirements(order, account))
        violations.extend(self._check_position_size_limits(order, account))
        violations.extend(self._check_leverage_limits(order, account))
        violations.extend(self._check_position_count_limits(order, account))
        violations.extend(self._check_daily_loss_limits(order, account))
        violations.extend(self._check_concentration_limits(order, account))
        violations.extend(self._check_portfolio_heat(order, account))

        # Store violations
        self.violation_history.extend(violations)

        # Determine if order should be rejected
        # Count ERROR level violations
        errors = [v for v in violations if v.severity == "ERROR"]
        warnings = [v for v in violations if v.severity == "WARNING"]

        if errors:
            logger.warning(
                f"Order {order.order_id} REJECTED due to {len(errors)} risk violations"
            )
            for violation in errors:
                logger.warning(f"  - {violation.message}")

        if warnings and self.config.allow_warnings:
            logger.info(
                f"Order {order.order_id} has {len(warnings)} risk warnings (allowed)"
            )
            for violation in warnings:
                logger.info(f"  - {violation.message}")

        # Reject if any ERROR violations
        is_valid = len(errors) == 0

        return is_valid, violations

    def _check_capital_requirements(
        self,
        order: Order,
        account: Account
    ) -> List[RiskViolation]:
        """Check if sufficient capital is available"""
        violations = []

        # Calculate order value
        estimated_price = order.limit_price or Decimal("0")
        if estimated_price == 0:
            # For market orders, would need current price
            # For now, skip this check
            return violations

        order_value = order.quantity * estimated_price * order.asset.multiplier

        # Check available capital (considering reserve)
        available = account.available_cash
        required_reserve = account.total_equity * self.config.reserve_capital_pct
        available_for_trading = available - required_reserve

        if order.side == OrderSide.BUY:
            if order_value > available_for_trading:
                violations.append(RiskViolation(
                    violation_type=RiskViolationType.INSUFFICIENT_CAPITAL,
                    message=(
                        f"Insufficient capital: need ${order_value:,.2f}, "
                        f"available ${available_for_trading:,.2f} "
                        f"(after ${required_reserve:,.2f} reserve)"
                    ),
                    current_value=available_for_trading,
                    limit_value=order_value,
                    severity="ERROR"
                ))

        # Check minimum equity requirement
        if self.config.min_equity and account.total_equity < self.config.min_equity:
            violations.append(RiskViolation(
                violation_type=RiskViolationType.MIN_EQUITY_BREACHED,
                message=(
                    f"Account equity ${account.total_equity:,.2f} below "
                    f"minimum ${self.config.min_equity:,.2f}"
                ),
                current_value=account.total_equity,
                limit_value=self.config.min_equity,
                severity="ERROR"
            ))

        return violations

    def _check_position_size_limits(
        self,
        order: Order,
        account: Account
    ) -> List[RiskViolation]:
        """Check position size limits"""
        violations = []

        if not self.config.enforce_position_limits:
            return violations

        # Calculate new position size
        current_position = account.get_position(order.asset)
        current_quantity = current_position.quantity if current_position else Decimal("0")

        if order.side == OrderSide.BUY:
            new_quantity = current_quantity + order.quantity
        else:
            new_quantity = current_quantity - order.quantity

        # Estimate position value
        estimated_price = order.limit_price or Decimal("100")  # Would use current price
        new_position_value = abs(new_quantity) * estimated_price * order.asset.multiplier

        # Check percentage limit
        max_value_pct = account.total_equity * self.config.max_position_size_pct
        if new_position_value > max_value_pct:
            violations.append(RiskViolation(
                violation_type=RiskViolationType.POSITION_SIZE_EXCEEDED,
                message=(
                    f"Position size ${new_position_value:,.2f} exceeds "
                    f"{self.config.max_position_size_pct*100}% limit "
                    f"(${max_value_pct:,.2f})"
                ),
                current_value=new_position_value,
                limit_value=max_value_pct,
                severity="ERROR"
            ))

        # Check absolute limit
        if self.config.max_position_value:
            if new_position_value > self.config.max_position_value:
                violations.append(RiskViolation(
                    violation_type=RiskViolationType.POSITION_SIZE_EXCEEDED,
                    message=(
                        f"Position size ${new_position_value:,.2f} exceeds "
                        f"absolute limit ${self.config.max_position_value:,.2f}"
                    ),
                    current_value=new_position_value,
                    limit_value=self.config.max_position_value,
                    severity="ERROR"
                ))

        return violations

    def _check_leverage_limits(
        self,
        order: Order,
        account: Account
    ) -> List[RiskViolation]:
        """Check leverage limits"""
        violations = []

        if not self.config.enforce_leverage_limits:
            return violations

        # Calculate total position value after this order
        total_position_value = sum(
            pos.market_value for pos in account.positions.values()
        )

        # Add this order's value
        estimated_price = order.limit_price or Decimal("100")
        if order.side == OrderSide.BUY:
            order_value = order.quantity * estimated_price * order.asset.multiplier
            total_position_value += order_value

        # Calculate leverage
        if account.total_equity > 0:
            leverage = total_position_value / account.total_equity

            if leverage > self.config.max_leverage:
                violations.append(RiskViolation(
                    violation_type=RiskViolationType.LEVERAGE_EXCEEDED,
                    message=(
                        f"Leverage {leverage:.2f}x exceeds "
                        f"limit {self.config.max_leverage:.2f}x"
                    ),
                    current_value=leverage,
                    limit_value=self.config.max_leverage,
                    severity="ERROR"
                ))

        return violations

    def _check_position_count_limits(
        self,
        order: Order,
        account: Account
    ) -> List[RiskViolation]:
        """Check maximum number of positions"""
        violations = []

        # Count open positions
        open_positions = len([p for p in account.positions.values() if p.is_open])

        # Check if this would create a new position
        current_position = account.get_position(order.asset)
        would_create_new = not current_position or not current_position.is_open

        if would_create_new and order.side == OrderSide.BUY:
            if open_positions >= self.config.max_open_positions:
                violations.append(RiskViolation(
                    violation_type=RiskViolationType.MAX_POSITIONS_EXCEEDED,
                    message=(
                        f"Already at maximum {self.config.max_open_positions} "
                        f"open positions"
                    ),
                    current_value=Decimal(str(open_positions)),
                    limit_value=Decimal(str(self.config.max_open_positions)),
                    severity="ERROR"
                ))

        return violations

    def _check_daily_loss_limits(
        self,
        order: Order,
        account: Account
    ) -> List[RiskViolation]:
        """Check daily loss circuit breaker"""
        violations = []

        if not self.config.enforce_daily_loss_limits:
            return violations

        today = date.today().isoformat()

        # Initialize tracking for today if needed
        if today not in self._daily_start_equity:
            self._daily_start_equity[today] = account.initial_balance
            self._daily_pnl[today] = Decimal("0")

        # Calculate current daily P&L
        start_equity = self._daily_start_equity[today]
        current_equity = account.total_equity
        daily_pnl = current_equity - start_equity
        daily_pnl_pct = (daily_pnl / start_equity * 100) if start_equity > 0 else Decimal("0")

        # Check percentage limit
        if daily_pnl_pct < -self.config.max_daily_loss_pct * 100:
            violations.append(RiskViolation(
                violation_type=RiskViolationType.DAILY_LOSS_LIMIT_EXCEEDED,
                message=(
                    f"Daily loss {daily_pnl_pct:.2f}% exceeds "
                    f"limit {self.config.max_daily_loss_pct*100:.2f}% "
                    f"(CIRCUIT BREAKER TRIGGERED)"
                ),
                current_value=abs(daily_pnl_pct),
                limit_value=self.config.max_daily_loss_pct * 100,
                severity="ERROR"
            ))

        # Check absolute limit
        if self.config.max_daily_loss_absolute:
            if abs(daily_pnl) > self.config.max_daily_loss_absolute:
                violations.append(RiskViolation(
                    violation_type=RiskViolationType.DAILY_LOSS_LIMIT_EXCEEDED,
                    message=(
                        f"Daily loss ${abs(daily_pnl):,.2f} exceeds "
                        f"absolute limit ${self.config.max_daily_loss_absolute:,.2f}"
                    ),
                    current_value=abs(daily_pnl),
                    limit_value=self.config.max_daily_loss_absolute,
                    severity="ERROR"
                ))

        return violations

    def _check_concentration_limits(
        self,
        order: Order,
        account: Account
    ) -> List[RiskViolation]:
        """Check concentration limits by sector and asset type"""
        violations = []

        if not self.config.enforce_concentration_limits:
            return violations

        # Group positions by asset type
        positions_by_type = {}
        for pos in account.positions.values():
            if pos.is_open:
                asset_type = pos.asset.asset_type.value
                if asset_type not in positions_by_type:
                    positions_by_type[asset_type] = Decimal("0")
                positions_by_type[asset_type] += pos.market_value

        # Add this order's contribution
        estimated_price = order.limit_price or Decimal("100")
        order_value = order.quantity * estimated_price * order.asset.multiplier
        asset_type = order.asset.asset_type.value

        if asset_type not in positions_by_type:
            positions_by_type[asset_type] = Decimal("0")
        positions_by_type[asset_type] += order_value

        # Check asset type concentration
        concentration_pct = (positions_by_type[asset_type] / account.total_equity * 100
                           if account.total_equity > 0 else Decimal("0"))

        max_concentration = self.config.max_asset_type_concentration_pct * 100
        if concentration_pct > max_concentration:
            violations.append(RiskViolation(
                violation_type=RiskViolationType.POSITION_CONCENTRATION_EXCEEDED,
                message=(
                    f"Asset type {asset_type} concentration {concentration_pct:.2f}% "
                    f"exceeds limit {max_concentration:.2f}%"
                ),
                current_value=concentration_pct,
                limit_value=max_concentration,
                severity="WARNING"  # Warning, not error
            ))

        return violations

    def _check_portfolio_heat(
        self,
        order: Order,
        account: Account
    ) -> List[RiskViolation]:
        """
        Check total portfolio heat (risk exposure).

        Portfolio heat = total potential loss if all positions hit stops
        """
        violations = []

        # Simplified: estimate based on position sizes
        # In practice, would use actual stop losses
        total_exposure = sum(
            pos.market_value for pos in account.positions.values() if pos.is_open
        )

        # Add this order
        estimated_price = order.limit_price or Decimal("100")
        order_value = order.quantity * estimated_price * order.asset.multiplier
        if order.side == OrderSide.BUY:
            total_exposure += order_value

        # Assume potential loss = position value * risk per trade
        estimated_heat = total_exposure * self.config.max_risk_per_trade_pct

        max_heat = account.total_equity * self.config.max_portfolio_heat_pct

        if estimated_heat > max_heat:
            violations.append(RiskViolation(
                violation_type=RiskViolationType.PORTFOLIO_HEAT_EXCEEDED,
                message=(
                    f"Portfolio heat ${estimated_heat:,.2f} exceeds "
                    f"limit ${max_heat:,.2f} "
                    f"({self.config.max_portfolio_heat_pct*100}% of equity)"
                ),
                current_value=estimated_heat,
                limit_value=max_heat,
                severity="WARNING"
            ))

        return violations

    def update_daily_equity(self, account: Account) -> None:
        """
        Update daily equity tracking.

        Should be called at start of each trading day.
        """
        today = date.today().isoformat()
        if today not in self._daily_start_equity:
            self._daily_start_equity[today] = account.total_equity
            logger.info(f"Daily equity tracking initialized: ${account.total_equity:,.2f}")

    def get_risk_metrics(self, account: Account) -> Dict[str, float]:
        """
        Calculate current risk metrics.

        Returns:
            Dictionary of risk metrics
        """
        # Current leverage
        total_position_value = sum(
            pos.market_value for pos in account.positions.values()
        )
        leverage = float(total_position_value / account.total_equity) if account.total_equity > 0 else 0.0

        # Daily P&L
        today = date.today().isoformat()
        start_equity = self._daily_start_equity.get(today, account.initial_balance)
        daily_pnl = account.total_equity - start_equity
        daily_pnl_pct = float(daily_pnl / start_equity * 100) if start_equity > 0 else 0.0

        # Open positions
        open_positions = len([p for p in account.positions.values() if p.is_open])

        # Available capital
        available_pct = float(account.available_cash / account.total_equity * 100) if account.total_equity > 0 else 0.0

        return {
            "leverage": leverage,
            "max_leverage": float(self.config.max_leverage),
            "daily_pnl": float(daily_pnl),
            "daily_pnl_pct": daily_pnl_pct,
            "max_daily_loss_pct": float(self.config.max_daily_loss_pct * 100),
            "open_positions": open_positions,
            "max_open_positions": self.config.max_open_positions,
            "available_capital_pct": available_pct,
            "total_equity": float(account.total_equity),
            "cash_balance": float(account.cash_balance),
            "violations_count": len(self.violation_history),
        }

    def reset_daily_tracking(self) -> None:
        """Reset daily tracking (for testing or new trading day)"""
        self._daily_pnl.clear()
        self._daily_start_equity.clear()
        logger.info("Daily risk tracking reset")

    def get_violation_summary(self) -> Dict[str, int]:
        """Get summary of violations"""
        summary = {}
        for violation in self.violation_history:
            vtype = violation.violation_type.value
            summary[vtype] = summary.get(vtype, 0) + 1
        return summary
