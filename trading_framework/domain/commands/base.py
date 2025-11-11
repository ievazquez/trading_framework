"""Base command class"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict
import uuid


@dataclass
class Command:
    """
    Base class for all commands in the system.

    Commands represent intentions to perform an action.
    They are imperative and should be named as verbs.
    """
    command_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def command_type(self) -> str:
        """Return the command type (class name)"""
        return self.__class__.__name__
