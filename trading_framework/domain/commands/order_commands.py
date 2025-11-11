"""Order-related commands"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Any

from .base import Command


@dataclass
class SubmitOrder(Command):
    """Command to submit a new order"""
    order: Any = None  # Order object
    account_id: str = None


@dataclass
class CancelOrder(Command):
    """Command to cancel an existing order"""
    order_id: str = None
    account_id: str = None
    reason: Optional[str] = None


@dataclass
class ModifyOrder(Command):
    """Command to modify an existing order"""
    order_id: str = None
    account_id: str = None
    new_quantity: Optional[Decimal] = None
    new_limit_price: Optional[Decimal] = None
    new_stop_price: Optional[Decimal] = None
