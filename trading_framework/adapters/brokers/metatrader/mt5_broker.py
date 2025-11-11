"""
MetaTrader 5 Adapter

Integrates with MetaTrader 5 terminal for forex and CFD trading.
MT5 must be installed and running on Windows.

Installation:
    pip install MetaTrader5

Configuration example:
    {
        "login": 12345678,
        "password": "your_password",
        "server": "MetaQuotes-Demo",
        "terminal_path": "C:\\Program Files\\MetaTrader 5\\terminal64.exe"
    }

Note: MT5 API only works on Windows. For Linux/Mac, consider using
a bridge via sockets or running MT5 in Wine.
"""

import logging
from typing import List, Optional, Callable
from decimal import Decimal

from ..base import AbstractBroker, ConnectionStatus
from ....domain.model import Order, Position, Account, Asset, Bar, Tick


logger = logging.getLogger(__name__)


class MetaTrader5Broker(AbstractBroker):
    """
    MetaTrader 5 adapter.

    Requires MT5 terminal running on Windows.
    API is synchronous, so we wrap it with async.
    """

    def __init__(self, config: dict):
        super().__init__("MetaTrader5", config)
        self.login = config.get("login")
        self.password = config.get("password")
        self.server = config.get("server")
        self.terminal_path = config.get("terminal_path")
        self.mt5 = None  # Would import MetaTrader5

    async def connect(self) -> bool:
        """
        Connect to MT5 terminal.

        MT5 must be running before connection.
        """
        try:
            # TODO: import MetaTrader5 as mt5
            # if not mt5.initialize(path=self.terminal_path):
            #     raise Exception(f"MT5 initialize failed: {mt5.last_error()}")
            # if not mt5.login(self.login, self.password, self.server):
            #     raise Exception(f"MT5 login failed: {mt5.last_error()}")

            logger.warning("MetaTrader5.connect not yet implemented")
            self.connection.status = ConnectionStatus.CONNECTED
            return True
        except Exception as e:
            logger.error(f"Failed to connect to MT5: {e}")
            self.connection.status = ConnectionStatus.ERROR
            return False

    async def disconnect(self) -> None:
        """Disconnect from MT5"""
        # TODO: mt5.shutdown()
        self.connection.status = ConnectionStatus.DISCONNECTED

    def is_connected(self) -> bool:
        return self.connection.is_connected()

    async def get_account(self, account_id: str) -> Optional[Account]:
        """Get MT5 account info"""
        # TODO: account_info = mt5.account_info()
        logger.warning("MetaTrader5.get_account not yet implemented")
        return None

    async def get_positions(self, account_id: str) -> List[Position]:
        """Get open positions from MT5"""
        # TODO: positions = mt5.positions_get()
        logger.warning("MetaTrader5.get_positions not yet implemented")
        return []

    async def get_position(self, account_id: str, asset: Asset) -> Optional[Position]:
        logger.warning("MetaTrader5.get_position not yet implemented")
        return None

    async def submit_order(self, order: Order) -> str:
        """
        Submit order to MT5.

        MT5 uses a different order model (ticket-based).
        """
        # TODO: Implement using mt5.order_send()
        # Must convert Order to MT5 TradeRequest format
        logger.warning("MetaTrader5.submit_order not yet implemented")
        raise NotImplementedError

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel pending order in MT5"""
        # TODO: Use mt5.order_send() with ACTION_REMOVE
        logger.warning("MetaTrader5.cancel_order not yet implemented")
        return False

    async def modify_order(self, order_id: str, **kwargs) -> bool:
        """Modify pending order"""
        # TODO: Use mt5.order_send() with ACTION_MODIFY
        logger.warning("MetaTrader5.modify_order not yet implemented")
        return False

    async def get_order(self, order_id: str) -> Optional[Order]:
        logger.warning("MetaTrader5.get_order not yet implemented")
        return None

    async def get_orders(self, account_id: str, active_only: bool = False) -> List[Order]:
        """Get orders from MT5"""
        # TODO: orders = mt5.orders_get()
        logger.warning("MetaTrader5.get_orders not yet implemented")
        return []

    async def get_latest_price(self, asset: Asset) -> Optional[Decimal]:
        """Get current tick price"""
        # TODO: tick = mt5.symbol_info_tick(asset.symbol)
        logger.warning("MetaTrader5.get_latest_price not yet implemented")
        return None

    async def get_latest_bar(self, asset: Asset) -> Optional[Bar]:
        """Get latest bar from MT5"""
        # TODO: rates = mt5.copy_rates_from_pos(asset.symbol, timeframe, 0, 1)
        logger.warning("MetaTrader5.get_latest_bar not yet implemented")
        return None

    async def subscribe_bars(self, asset: Asset, callback: Callable[[Bar], None]) -> None:
        """
        Subscribe to bars.

        MT5 doesn't have push notifications, so we need to poll.
        """
        logger.warning("MetaTrader5.subscribe_bars not yet implemented")

    async def subscribe_ticks(self, asset: Asset, callback: Callable[[Tick], None]) -> None:
        """Subscribe to tick data (polling)"""
        logger.warning("MetaTrader5.subscribe_ticks not yet implemented")

    async def unsubscribe(self, asset: Asset) -> None:
        logger.warning("MetaTrader5.unsubscribe not yet implemented")

    async def search_assets(self, query: str) -> List[Asset]:
        """Search MT5 symbols"""
        # TODO: symbols = mt5.symbols_get(query)
        logger.warning("MetaTrader5.search_assets not yet implemented")
        return []

    async def get_asset(self, symbol: str) -> Optional[Asset]:
        """Get symbol info from MT5"""
        # TODO: symbol_info = mt5.symbol_info(symbol)
        logger.warning("MetaTrader5.get_asset not yet implemented")
        return None

    def normalize_symbol(self, symbol: str) -> str:
        """MT5 symbols often have suffixes like .r or .m"""
        return symbol

    def denormalize_symbol(self, symbol: str) -> str:
        return symbol
