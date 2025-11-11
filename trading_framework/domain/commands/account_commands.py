"""Account-related commands"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from .base import Command


@dataclass
class UpdateAccountBalance(Command):
    """Command to update account balance"""
    account_id: str = None
    amount: Decimal = None
    reason: Optional[str] = None


@dataclass
class CloseAllPositions(Command):
    """Command to close all positions in an account"""
    account_id: str = None
    reason: Optional[str] = None
