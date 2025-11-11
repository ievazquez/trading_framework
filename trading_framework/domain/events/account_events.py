"""Account-related domain events"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from .base import DomainEvent


@dataclass
class AccountBalanceUpdated(DomainEvent):
    """Event emitted when account balance changes"""
    account_id: str = None
    cash_balance: Decimal = None
    total_equity: Decimal = None
    reason: Optional[str] = None

    def __post_init__(self):
        if not self.aggregate_id:
            object.__setattr__(self, 'aggregate_id', self.account_id)
        super().__post_init__()
