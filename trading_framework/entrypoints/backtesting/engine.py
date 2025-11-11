"""
Backtesting Engine

Event-driven backtesting engine that simulates trading strategies
against historical data.

Features:
- Event-driven architecture
- Supports multiple data sources (CSV, PostgreSQL, APIs)
- Real-time and historical backtesting
- Comprehensive performance metrics
- Position and order tracking
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from decimal import Decimal

from ...domain.model import (
    Asset,
    Bar,
    BarResolution,
    Account,
    Order,
    Position,
)
from ...domain.events import BarReceived, OrderFilled
from ...adapters.brokers import SimulatedBroker
from ...adapters.repository.base import AbstractMarketDataRepository
from ...adapters.notifications import NotificationManager
from ...service_layer.unit_of_work import InMemoryUnitOfWork
from ...service_layer.messagebus import MessageBus
from ...service_layer.risk_manager import RiskManager, RiskConfig


logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """Configuration for a backtest"""

    # Time period
    start_date: datetime
    end_date: datetime

    # Assets to trade
    assets: List[Asset]
    resolution: BarResolution = BarResolution.MIN_1

    # Initial capital
    initial_capital: Decimal = Decimal("100000")
    currency: str = "USD"

    # Trading costs
    commission_per_share: Decimal = Decimal("0.01")
    slippage_pct: Decimal = Decimal("0.001")  # 0.1%

    # Risk management
    max_position_size_pct: Decimal = Decimal("0.1")  # 10% of portfolio
    max_leverage: Decimal = Decimal("1.0")  # No leverage by default
    max_open_positions: int = 10
    max_daily_loss_pct: Decimal = Decimal("0.05")  # 5% daily loss limit
    risk_config: Optional[RiskConfig] = None  # Optional custom risk config

    # Execution
    fill_immediately: bool = True

    # Notifications
    enable_notifications: bool = False  # Enable notifications during backtest
    notification_manager: Optional[NotificationManager] = None

    # Logging
    log_level: str = "INFO"


@dataclass
class BacktestResult:
    """Results of a backtest"""

    # Configuration
    config: BacktestConfig

    # Performance metrics
    total_return: Decimal = Decimal("0")
    total_return_pct: Decimal = Decimal("0")
    annualized_return: Decimal = Decimal("0")
    sharpe_ratio: Decimal = Decimal("0")
    max_drawdown: Decimal = Decimal("0")
    max_drawdown_pct: Decimal = Decimal("0")

    # Trade statistics
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: Decimal = Decimal("0")
    avg_win: Decimal = Decimal("0")
    avg_loss: Decimal = Decimal("0")
    profit_factor: Decimal = Decimal("0")

    # Execution metrics
    total_commission: Decimal = Decimal("0")
    total_slippage: Decimal = Decimal("0")

    # Risk metrics
    risk_violations: int = 0
    orders_rejected_by_risk: int = 0
    max_leverage_used: Decimal = Decimal("0")
    risk_violation_summary: Dict[str, int] = field(default_factory=dict)

    # Equity curve
    equity_curve: List[Dict] = field(default_factory=list)

    # Final account state
    final_equity: Decimal = Decimal("0")
    final_cash: Decimal = Decimal("0")
    final_positions: List[Position] = field(default_factory=list)

    # Timestamps
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0

    def print_summary(self) -> None:
        """Print a summary of backtest results"""
        print("\n" + "="*60)
        print("BACKTEST RESULTS")
        print("="*60)
        print(f"\nPeriod: {self.config.start_date} to {self.config.end_date}")
        print(f"Initial Capital: ${self.config.initial_capital:,.2f}")
        print(f"Final Equity: ${self.final_equity:,.2f}")
        print(f"\nPerformance:")
        print(f"  Total Return: ${self.total_return:,.2f} ({self.total_return_pct:.2f}%)")
        print(f"  Annualized Return: {self.annualized_return:.2f}%")
        print(f"  Sharpe Ratio: {self.sharpe_ratio:.2f}")
        print(f"  Max Drawdown: ${self.max_drawdown:,.2f} ({self.max_drawdown_pct:.2f}%)")
        print(f"\nTrades:")
        print(f"  Total Trades: {self.total_trades}")
        print(f"  Winning Trades: {self.winning_trades}")
        print(f"  Losing Trades: {self.losing_trades}")
        print(f"  Win Rate: {self.win_rate:.2f}%")
        print(f"  Profit Factor: {self.profit_factor:.2f}")
        print(f"\nCosts:")
        print(f"  Total Commission: ${self.total_commission:,.2f}")
        print(f"  Total Slippage: ${self.total_slippage:,.2f}")
        print(f"\nRisk Management:")
        print(f"  Orders Rejected by Risk: {self.orders_rejected_by_risk}")
        print(f"  Total Risk Violations: {self.risk_violations}")
        print(f"  Max Leverage Used: {self.max_leverage_used:.2f}x")
        if self.risk_violation_summary:
            print(f"  Violations by Type:")
            for vtype, count in self.risk_violation_summary.items():
                print(f"    - {vtype}: {count}")
        print(f"\nExecution Time: {self.duration_seconds:.2f} seconds")
        print("="*60 + "\n")


class BacktestEngine:
    """
    Event-driven backtesting engine.

    Replays historical data and simulates strategy execution.
    """

    def __init__(
        self,
        config: BacktestConfig,
        data_source: AbstractMarketDataRepository,
        strategy: Callable,
    ):
        """
        Initialize backtest engine.

        Args:
            config: Backtest configuration
            data_source: Source of historical data
            strategy: Strategy function/class to test
        """
        self.config = config
        self.data_source = data_source
        self.strategy = strategy

        # Set up logging
        logging.basicConfig(level=config.log_level)

        # Initialize components
        self.broker = SimulatedBroker({
            "commission_per_share": str(config.commission_per_share),
            "slippage_pct": str(config.slippage_pct),
            "fill_immediately": config.fill_immediately,
        })

        # Create account
        self.account = Account(
            account_id="backtest_account",
            broker="SimulatedBroker",
            cash_balance=config.initial_capital,
            initial_balance=config.initial_capital,
            currency=config.currency,
        )

        # Unit of Work and Message Bus
        self.uow = InMemoryUnitOfWork()
        self.message_bus = MessageBus()

        # Risk Manager
        if config.risk_config:
            self.risk_manager = RiskManager(config.risk_config)
        else:
            # Create default risk config from backtest config
            self.risk_manager = RiskManager(RiskConfig(
                max_position_size_pct=config.max_position_size_pct,
                max_leverage=config.max_leverage,
                max_open_positions=config.max_open_positions,
                max_daily_loss_pct=config.max_daily_loss_pct,
            ))

        # Notification Manager
        if config.notification_manager:
            self.notification_manager = config.notification_manager
        else:
            self.notification_manager = NotificationManager()

        self.enable_notifications = config.enable_notifications

        # Performance tracking
        self.equity_history: List[Dict] = []
        self.peak_equity = config.initial_capital
        self.max_drawdown = Decimal("0")

    async def run(self) -> BacktestResult:
        """
        Run the backtest.

        Returns:
            BacktestResult with performance metrics
        """
        logger.info(f"Starting backtest from {self.config.start_date} to {self.config.end_date}")
        start_time = datetime.utcnow()

        try:
            # Initialize
            await self._initialize()

            # Load historical data
            bars_by_asset = await self._load_data()

            if not bars_by_asset:
                raise ValueError("No historical data loaded")

            # Run backtest
            await self._run_backtest(bars_by_asset)

            # Calculate results
            result = await self._calculate_results(start_time)

            # Send backtest completion notification
            if self.enable_notifications:
                await self.notification_manager.notify_daily_summary(
                    pnl=float(result.total_return),
                    pnl_pct=float(result.total_return_pct),
                    trades_count=result.total_trades,
                    win_rate=float(result.win_rate),
                    final_equity=float(result.final_equity),
                    sharpe_ratio=float(result.sharpe_ratio),
                    max_drawdown=float(result.max_drawdown),
                )

            logger.info("Backtest completed successfully")
            return result

        except Exception as e:
            logger.error(f"Backtest failed: {e}", exc_info=True)
            raise

    async def _initialize(self) -> None:
        """Initialize broker and account"""
        await self.broker.connect()
        self.broker.add_account(self.account)

        # Store account in UoW
        self.uow.accounts.add(self.account)

        # Initialize risk manager daily tracking
        self.risk_manager.update_daily_equity(self.account)

        logger.info(f"Initialized account with ${self.config.initial_capital:,.2f}")

    async def _load_data(self) -> Dict[str, List[Bar]]:
        """Load historical data for all assets"""
        bars_by_asset = {}

        for asset in self.config.assets:
            bars = self.data_source.get_bars(
                asset=asset,
                resolution=self.config.resolution,
                start_date=self.config.start_date,
                end_date=self.config.end_date,
            )

            if bars:
                bars_by_asset[asset.full_symbol] = bars
                logger.info(f"Loaded {len(bars)} bars for {asset.symbol}")
            else:
                logger.warning(f"No data found for {asset.symbol}")

        return bars_by_asset

    async def _run_backtest(self, bars_by_asset: Dict[str, List[Bar]]) -> None:
        """
        Run the backtest by replaying bars chronologically.

        Merges bars from multiple assets and processes them in time order.
        """
        # Merge all bars and sort by timestamp
        all_bars = []
        for asset_bars in bars_by_asset.values():
            all_bars.extend(asset_bars)
        all_bars.sort(key=lambda b: b.timestamp)

        logger.info(f"Processing {len(all_bars)} total bars")

        # Process each bar
        for i, bar in enumerate(all_bars):
            # Update broker with new price
            self.broker.update_price(bar.asset, bar.close)

            # Update account positions with new prices
            prices = {bar.asset.full_symbol: bar.close}
            self.account.update_prices(prices)

            # Track equity
            self._record_equity(bar.timestamp)

            # Publish bar event to strategy
            event = BarReceived(bar=bar)
            await self._notify_strategy(event)

            # Log progress
            if (i + 1) % 1000 == 0:
                logger.info(f"Processed {i + 1}/{len(all_bars)} bars")

    async def _notify_strategy(self, event: BarReceived) -> None:
        """Notify strategy of new bar"""
        try:
            # Call strategy with bar and context
            context = {
                "account": self.account,
                "broker": self.broker,
                "uow": self.uow,
                "bar": event.bar,
                "risk_manager": self.risk_manager,
            }

            # Strategy can return orders to submit
            orders = self.strategy(context)

            if orders:
                if not isinstance(orders, list):
                    orders = [orders]

                for order in orders:
                    # Validate order with risk manager
                    is_valid, violations = self.risk_manager.validate_order(order, self.account)

                    if is_valid:
                        await self.broker.submit_order(order)

                        # Notify order executed (if notifications enabled)
                        if self.enable_notifications:
                            await self.notification_manager.notify_trade_executed(
                                asset_symbol=order.asset.symbol,
                                side=order.side.value,
                                quantity=float(order.quantity),
                                price=float(order.limit_price or 0),
                                order_id=order.order_id,
                                timestamp=event.bar.timestamp.isoformat()
                            )
                    else:
                        # Log risk violations
                        violation_msgs = [v.message for v in violations if v.severity == "ERROR"]
                        logger.warning(
                            f"Order {order.order_id} rejected by risk manager: "
                            f"{'; '.join(violation_msgs)}"
                        )

                        # Notify order rejected (if notifications enabled)
                        if self.enable_notifications:
                            await self.notification_manager.notify_order_rejected(
                                asset_symbol=order.asset.symbol,
                                side=order.side.value,
                                quantity=float(order.quantity),
                                reason="; ".join(violation_msgs),
                                order_id=order.order_id
                            )

        except Exception as e:
            logger.error(f"Error in strategy: {e}", exc_info=True)

    def _record_equity(self, timestamp: datetime) -> None:
        """Record current equity for performance tracking"""
        equity = self.account.total_equity

        # Track peak and drawdown
        if equity > self.peak_equity:
            self.peak_equity = equity
        drawdown = self.peak_equity - equity
        if drawdown > self.max_drawdown:
            self.max_drawdown = drawdown

        # Record equity point
        self.equity_history.append({
            "timestamp": timestamp,
            "equity": float(equity),
            "cash": float(self.account.cash_balance),
            "positions_value": float(sum(p.market_value for p in self.account.positions.values())),
            "drawdown": float(drawdown),
        })

    async def _calculate_results(self, start_time: datetime) -> BacktestResult:
        """Calculate final backtest metrics"""
        end_time = datetime.utcnow()

        # Final values
        final_equity = self.account.total_equity
        total_return = final_equity - self.config.initial_capital
        total_return_pct = (total_return / self.config.initial_capital) * 100

        # Annualized return
        days = (self.config.end_date - self.config.start_date).days
        years = days / 365.25
        annualized_return = ((final_equity / self.config.initial_capital) ** (1 / years) - 1) * 100 if years > 0 else 0

        # Calculate Sharpe ratio (simplified)
        if len(self.equity_history) > 1:
            returns = []
            for i in range(1, len(self.equity_history)):
                prev_equity = Decimal(str(self.equity_history[i-1]["equity"]))
                curr_equity = Decimal(str(self.equity_history[i]["equity"]))
                ret = (curr_equity - prev_equity) / prev_equity if prev_equity > 0 else Decimal("0")
                returns.append(float(ret))

            if returns:
                import statistics
                avg_return = statistics.mean(returns)
                std_return = statistics.stdev(returns) if len(returns) > 1 else 0
                sharpe_ratio = (avg_return / std_return * (252 ** 0.5)) if std_return > 0 else 0
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0

        # Trade statistics (would need to track individual trades)
        # For now, use simplified metrics
        total_trades = len([o for o in self.uow.orders.list() if o.status.value == "FILLED"])

        # Risk metrics
        risk_metrics = self.risk_manager.get_risk_metrics(self.account)
        violation_summary = self.risk_manager.get_violation_summary()
        total_violations = len(self.risk_manager.violation_history)

        # Count orders rejected
        rejected_orders = len([o for o in self.uow.orders.list() if o.status.value == "REJECTED"])

        result = BacktestResult(
            config=self.config,
            total_return=total_return,
            total_return_pct=total_return_pct,
            annualized_return=Decimal(str(annualized_return)),
            sharpe_ratio=Decimal(str(sharpe_ratio)),
            max_drawdown=self.max_drawdown,
            max_drawdown_pct=(self.max_drawdown / self.peak_equity * 100) if self.peak_equity > 0 else Decimal("0"),
            total_trades=total_trades,
            # Risk metrics
            risk_violations=total_violations,
            orders_rejected_by_risk=rejected_orders,
            max_leverage_used=Decimal(str(risk_metrics.get("leverage", 0))),
            risk_violation_summary=violation_summary,
            # Equity and positions
            equity_curve=self.equity_history,
            final_equity=final_equity,
            final_cash=self.account.cash_balance,
            final_positions=list(self.account.positions.values()),
            start_time=start_time,
            end_time=end_time,
            duration_seconds=(end_time - start_time).total_seconds(),
        )

        return result
