"""
Example: Running a Backtest

This script demonstrates how to run a backtest using the trading framework.
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
from strategies.simple_sma_crossover import SimpleSMACrossover


async def main():
    """Run a simple backtest"""

    print("="*60)
    print("TRADING FRAMEWORK - BACKTEST EXAMPLE")
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
    # Assumes CSV files in format: data/AAPL_1D.csv
    data_source = CSVDataSource({
        "data_dir": "./data",
        "filename_pattern": "{symbol}_{resolution}.csv",
        "date_format": "%Y-%m-%d %H:%M:%S"
    })

    # Configure backtest
    config = BacktestConfig(
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 12, 31),
        assets=[asset],
        resolution=BarResolution.DAY_1,
        initial_capital=Decimal("100000"),
        commission_per_share=Decimal("0.01"),
        slippage_pct=Decimal("0.001"),
    )

    # Create strategy
    strategy = SimpleSMACrossover(
        fast_period=10,
        slow_period=30,
        position_size_pct=0.5  # Use 50% of capital
    )

    # Create and run backtest engine
    print(f"\nInitializing backtest...")
    print(f"Asset: {asset.symbol}")
    print(f"Period: {config.start_date} to {config.end_date}")
    print(f"Initial Capital: ${config.initial_capital:,.2f}")
    print(f"Strategy: SMA Crossover (10/30)")

    engine = BacktestEngine(
        config=config,
        data_source=data_source,
        strategy=strategy,
    )

    # Run backtest
    print("\nRunning backtest...")
    result = await engine.run()

    # Print results
    result.print_summary()

    # Save equity curve to CSV
    if result.equity_curve:
        output_file = "backtest_equity_curve.csv"
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
        print("✅ Strategy was profitable!")
        sys.exit(0)
    else:
        print("❌ Strategy lost money")
        sys.exit(1)
