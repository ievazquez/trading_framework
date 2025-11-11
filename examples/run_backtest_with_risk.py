"""
Example: Running a Backtest with Risk Management

This script demonstrates how to run a backtest with comprehensive risk management.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_framework.domain.model import Asset, AssetType, BarResolution
from trading_framework.adapters.data_sources.csv import CSVDataSource
from trading_framework.entrypoints.backtesting import BacktestEngine, BacktestConfig
from trading_framework.service_layer.risk_manager import RiskConfig
from strategies.simple_sma_crossover import SimpleSMACrossover


async def main():
    """Run a backtest with risk management"""

    print("="*60)
    print("TRADING FRAMEWORK - BACKTEST WITH RISK MANAGEMENT")
    print("="*60)

    # Define the asset to trade
    asset = Asset(
        symbol="AAPL",
        asset_type=AssetType.STOCK,
        exchange="NASDAQ",
        currency="USD",
        min_quantity=Decimal("1"),
        quantity_increment=Decimal("1"),
        min_price_increment=Decimal("0.01"),
    )

    # Configure data source
    data_source = CSVDataSource({
        "data_dir": "./data",
        "filename_pattern": "{symbol}_{resolution}.csv",
        "date_format": "%Y-%m-%d %H:%M:%S"
    })

    # Configure comprehensive risk management
    risk_config = RiskConfig(
        # Position sizing
        max_position_size_pct=Decimal("0.15"),  # Max 15% per position
        max_position_value=Decimal("20000"),    # Max $20k per position

        # Leverage limits
        max_leverage=Decimal("1.5"),  # Allow up to 1.5x leverage

        # Portfolio limits
        max_open_positions=5,  # Max 5 concurrent positions
        max_positions_per_asset=1,

        # Circuit breakers
        max_daily_loss_pct=Decimal("0.03"),  # Stop trading if lose 3% in a day
        max_daily_loss_absolute=Decimal("3000"),  # Or $3000

        # Capital management
        min_equity=Decimal("50000"),  # Stop if equity drops below $50k
        reserve_capital_pct=Decimal("0.15"),  # Keep 15% in reserve

        # Concentration limits
        max_sector_concentration_pct=Decimal("0.4"),  # Max 40% per sector
        max_asset_type_concentration_pct=Decimal("0.6"),  # Max 60% per asset type

        # Portfolio risk
        max_portfolio_heat_pct=Decimal("0.15"),  # Max 15% total risk
        max_risk_per_trade_pct=Decimal("0.02"),  # Max 2% risk per trade

        # Enforcement flags
        enforce_position_limits=True,
        enforce_leverage_limits=True,
        enforce_daily_loss_limits=True,
        enforce_concentration_limits=True,
        allow_warnings=True,  # Allow warnings without rejection
    )

    # Configure backtest
    config = BacktestConfig(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        assets=[asset],
        resolution=BarResolution.DAY_1,
        initial_capital=Decimal("100000"),
        commission_per_share=Decimal("0.01"),
        slippage_pct=Decimal("0.001"),
        # Pass custom risk config
        risk_config=risk_config,
    )

    # Create strategy
    strategy = SimpleSMACrossover(
        fast_period=10,
        slow_period=30,
        position_size_pct=0.15  # Try to use 15% per position
    )

    # Create and run backtest engine
    print(f"\nInitializing backtest...")
    print(f"Asset: {asset.symbol}")
    print(f"Period: {config.start_date} to {config.end_date}")
    print(f"Initial Capital: ${config.initial_capital:,.2f}")
    print(f"Strategy: SMA Crossover (10/30)")
    print(f"\nRisk Management Configuration:")
    print(f"  Max Position Size: {risk_config.max_position_size_pct*100}%")
    print(f"  Max Leverage: {risk_config.max_leverage}x")
    print(f"  Max Open Positions: {risk_config.max_open_positions}")
    print(f"  Max Daily Loss: {risk_config.max_daily_loss_pct*100}%")
    print(f"  Circuit Breaker: ${risk_config.max_daily_loss_absolute:,.2f}")

    engine = BacktestEngine(
        config=config,
        data_source=data_source,
        strategy=strategy,
    )

    # Run backtest
    print("\nRunning backtest with risk management...")
    result = await engine.run()

    # Print results
    result.print_summary()

    # Print additional risk analysis
    print("\n" + "="*60)
    print("RISK MANAGEMENT ANALYSIS")
    print("="*60)
    print(f"\nRisk Protection:")
    print(f"  Orders Submitted: {result.total_trades + result.orders_rejected_by_risk}")
    print(f"  Orders Accepted: {result.total_trades}")
    print(f"  Orders Rejected: {result.orders_rejected_by_risk}")
    if result.total_trades + result.orders_rejected_by_risk > 0:
        rejection_rate = (result.orders_rejected_by_risk /
                         (result.total_trades + result.orders_rejected_by_risk) * 100)
        print(f"  Rejection Rate: {rejection_rate:.2f}%")

    if result.risk_violation_summary:
        print(f"\nViolation Breakdown:")
        for vtype, count in sorted(result.risk_violation_summary.items(),
                                   key=lambda x: x[1], reverse=True):
            print(f"  {vtype}: {count}")

    print(f"\nLeverage Usage:")
    print(f"  Maximum Leverage: {result.max_leverage_used:.2f}x")
    print(f"  Leverage Limit: {risk_config.max_leverage}x")
    if result.max_leverage_used <= risk_config.max_leverage:
        print(f"  Status: ✅ Within limits")
    else:
        print(f"  Status: ⚠️  Exceeded limits")

    print("="*60 + "\n")

    # Save equity curve to CSV
    if result.equity_curve:
        output_file = "backtest_equity_curve_with_risk.csv"
        print(f"Saving equity curve to {output_file}...")

        import csv
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=result.equity_curve[0].keys())
            writer.writeheader()
            writer.writerows(result.equity_curve)

        print(f"Equity curve saved!")

    return result


if __name__ == "__main__":
    # Run the async main function
    result = asyncio.run(main())

    # Exit with appropriate code
    if result.total_return > 0:
        print("✅ Strategy was profitable with risk management!")
        sys.exit(0)
    else:
        print("❌ Strategy lost money (but risk was managed)")
        sys.exit(1)
