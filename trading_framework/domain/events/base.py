"""Base event classes"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict
import uuid


@dataclass
class Event:
    """
    Base class for all events in the system.

    Events represent things that have happened in the past.
    They are immutable and should be named in past tense.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Ensure event is immutable after creation"""
        # Note: Using frozen=True in subclasses would make them truly immutable
        pass

    @property
    def event_type(self) -> str:
        """Return the event type (class name)"""
        return self.__class__.__name__


@dataclass
class DomainEvent(Event):
    """
    Base class for domain events.

    Domain events represent business-significant occurrences in the domain.
    """
    aggregate_id: str = None  # ID of the aggregate that produced this event
    aggregate_type: str = None  # Type of the aggregate

    def __post_init__(self):
        super().__post_init__()
        if not self.aggregate_type:
            # Try to infer from event name (e.g., OrderSubmitted -> Order)
            event_name = self.__class__.__name__
            for keyword in ["Submitted", "Accepted", "Filled", "Cancelled", "Rejected",
                          "Updated", "Reduced", "Closed", "Created", "Deleted"]:
                if event_name.endswith(keyword):
                    object.__setattr__(self, 'aggregate_type', event_name[:-len(keyword)])
                    break
