"""
Alpaca Adapter

Integrates with Alpaca Markets API for US stocks trading.
Commission-free trading with real-time data.

Installation:
    pip install alpaca-trade-api

Configuration example:
    {
        "api_key": "your_api_key",
        "api_secret": "your_api_secret",
        "base_url": "https://paper-api.alpaca.markets",  # Paper trading
        "data_feed": "iex"  # iex or sip
    }
"""

import logging
from typing import List, Optional, Callable
from decimal import Decimal

from ..base import AbstractBroker, ConnectionStatus
from ....domain.model import Order, Position, Account, Asset, Bar, Tick


logger = logging.getLogger(__name__)


class AlpacaBroker(AbstractBroker):
    """Alpaca Markets adapter for US stocks"""

    def __init__(self, config: dict):
        super().__init__("Alpaca", config)
        self.api_key = config.get("api_key")
        self.api_secret = config.get("api_secret")
        self.base_url = config.get("base_url", "https://paper-api.alpaca.markets")
        self.api = None  # Would use alpaca_trade_api.REST

    async def connect(self) -> bool:
        """Connect to Alpaca API"""
        # TODO: from alpaca_trade_api import REST
        # self.api = REST(self.api_key, self.api_secret, self.base_url)
        logger.warning("Alpaca.connect not yet implemented")
        self.connection.status = ConnectionStatus.CONNECTED
        return True

    async def disconnect(self) -> None:
        self.connection.status = ConnectionStatus.DISCONNECTED

    def is_connected(self) -> bool:
        return self.connection.is_connected()

    async def get_account(self, account_id: str) -> Optional[Account]:
        # TODO: account = self.api.get_account()
        logger.warning("Alpaca.get_account not yet implemented")
        return None

    async def get_positions(self, account_id: str) -> List[Position]:
        # TODO: positions = self.api.list_positions()
        logger.warning("Alpaca.get_positions not yet implemented")
        return []

    async def get_position(self, account_id: str, asset: Asset) -> Optional[Position]:
        logger.warning("Alpaca.get_position not yet implemented")
        return None

    async def submit_order(self, order: Order) -> str:
        # TODO: alpaca_order = self.api.submit_order(...)
        logger.warning("Alpaca.submit_order not yet implemented")
        raise NotImplementedError

    async def cancel_order(self, order_id: str) -> bool:
        logger.warning("Alpaca.cancel_order not yet implemented")
        return False

    async def modify_order(self, order_id: str, **kwargs) -> bool:
        logger.warning("Alpaca.modify_order not yet implemented")
        return False

    async def get_order(self, order_id: str) -> Optional[Order]:
        logger.warning("Alpaca.get_order not yet implemented")
        return None

    async def get_orders(self, account_id: str, active_only: bool = False) -> List[Order]:
        logger.warning("Alpaca.get_orders not yet implemented")
        return []

    async def get_latest_price(self, asset: Asset) -> Optional[Decimal]:
        logger.warning("Alpaca.get_latest_price not yet implemented")
        return None

    async def get_latest_bar(self, asset: Asset) -> Optional[Bar]:
        logger.warning("Alpaca.get_latest_bar not yet implemented")
        return None

    async def subscribe_bars(self, asset: Asset, callback: Callable[[Bar], None]) -> None:
        logger.warning("Alpaca.subscribe_bars not yet implemented")

    async def subscribe_ticks(self, asset: Asset, callback: Callable[[Tick], None]) -> None:
        logger.warning("Alpaca.subscribe_ticks not yet implemented")

    async def unsubscribe(self, asset: Asset) -> None:
        logger.warning("Alpaca.unsubscribe not yet implemented")

    async def search_assets(self, query: str) -> List[Asset]:
        logger.warning("Alpaca.search_assets not yet implemented")
        return []

    async def get_asset(self, symbol: str) -> Optional[Asset]:
        logger.warning("Alpaca.get_asset not yet implemented")
        return None
