"""
CSV Data Source

Reads OHLCV data from CSV files for backtesting.

Expected CSV format:
    timestamp,open,high,low,close,volume
    2024-01-01 00:00:00,100.0,101.0,99.0,100.5,1000000
    ...

Configuration example:
    {
        "data_dir": "/path/to/csv/files",
        "filename_pattern": "{symbol}_{resolution}.csv",
        "date_format": "%Y-%m-%d %H:%M:%S"
    }
"""

import logging
import csv
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from decimal import Decimal

from ...repository.base import AbstractMarketDataRepository
from ....domain.model import Asset, Bar, Tick, BarResolution


logger = logging.getLogger(__name__)


class CSVDataSource(AbstractMarketDataRepository):
    """
    CSV file data source for historical OHLCV data.

    Reads bars from CSV files organized by symbol and resolution.
    """

    def __init__(self, config: dict):
        self.data_dir = Path(config.get("data_dir", "./data"))
        self.filename_pattern = config.get("filename_pattern", "{symbol}_{resolution}.csv")
        self.date_format = config.get("date_format", "%Y-%m-%d %H:%M:%S")

        # Cache loaded data
        self._cache = {}

    def get_bars(
        self,
        asset: Asset,
        resolution: BarResolution,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Bar]:
        """Read bars from CSV file"""
        # Generate filename
        filename = self.filename_pattern.format(
            symbol=asset.symbol,
            resolution=resolution.value
        )
        filepath = self.data_dir / filename

        if not filepath.exists():
            logger.warning(f"CSV file not found: {filepath}")
            return []

        # Check cache
        cache_key = (asset.full_symbol, resolution.value)
        if cache_key not in self._cache:
            self._cache[cache_key] = self._load_csv(filepath, asset, resolution)

        # Filter by date range
        bars = self._cache[cache_key]
        filtered = [
            bar for bar in bars
            if start_date <= bar.timestamp <= end_date
        ]

        logger.info(
            f"Loaded {len(filtered)} bars for {asset.symbol} "
            f"from {start_date} to {end_date}"
        )
        return filtered

    def _load_csv(
        self,
        filepath: Path,
        asset: Asset,
        resolution: BarResolution
    ) -> List[Bar]:
        """Load and parse CSV file"""
        bars = []

        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    try:
                        # Parse timestamp
                        timestamp = datetime.strptime(
                            row['timestamp'],
                            self.date_format
                        )

                        # Create Bar object
                        bar = Bar(
                            asset=asset,
                            timestamp=timestamp,
                            resolution=resolution,
                            open=Decimal(row['open']),
                            high=Decimal(row['high']),
                            low=Decimal(row['low']),
                            close=Decimal(row['close']),
                            volume=Decimal(row.get('volume', '0')),
                            # Optional fields
                            vwap=Decimal(row['vwap']) if 'vwap' in row else None,
                            trades_count=int(row['trades']) if 'trades' in row else None,
                        )
                        bars.append(bar)

                    except Exception as e:
                        logger.error(f"Error parsing CSV row: {e}")
                        continue

            logger.info(f"Loaded {len(bars)} bars from {filepath}")
            return bars

        except Exception as e:
            logger.error(f"Error loading CSV file {filepath}: {e}", exc_info=True)
            return []

    def get_ticks(
        self,
        asset: Asset,
        start_date: datetime,
        end_date: datetime,
    ) -> List[Tick]:
        """
        Get ticks from CSV (similar format as bars but with tick data).

        Not commonly used - most CSV data is in OHLCV format.
        """
        logger.warning("CSV tick data not yet implemented")
        return []

    def get_latest_bar(self, asset: Asset, resolution: BarResolution) -> Optional[Bar]:
        """Get the most recent bar for an asset"""
        cache_key = (asset.full_symbol, resolution.value)
        if cache_key in self._cache and self._cache[cache_key]:
            return self._cache[cache_key][-1]
        return None

    def get_latest_price(self, asset: Asset) -> Optional[Decimal]:
        """Get latest price from the most recent bar"""
        for resolution in [BarResolution.MIN_1, BarResolution.MIN_5, BarResolution.DAY_1]:
            bar = self.get_latest_bar(asset, resolution)
            if bar:
                return bar.close
        return None

    def preload_data(self, assets: List[Asset], resolutions: List[BarResolution]) -> None:
        """
        Preload data for multiple assets and resolutions.

        Useful for backtesting to avoid repeated file I/O.
        """
        for asset in assets:
            for resolution in resolutions:
                filename = self.filename_pattern.format(
                    symbol=asset.symbol,
                    resolution=resolution.value
                )
                filepath = self.data_dir / filename

                if filepath.exists():
                    cache_key = (asset.full_symbol, resolution.value)
                    if cache_key not in self._cache:
                        self._cache[cache_key] = self._load_csv(filepath, asset, resolution)

        logger.info(f"Preloaded data for {len(assets)} assets")
