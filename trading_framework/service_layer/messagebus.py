"""
Message Bus Implementation

The message bus is the central nervous system of the event-driven architecture.
It handles both Commands (intentions) and Events (facts).

Commands:
- Are imperative (e.g., "SubmitOrder")
- Have exactly one handler
- Can fail
- Represent intentions to change state

Events:
- Are declarative (e.g., "OrderSubmitted")
- Can have zero or more handlers
- Should not fail (if one handler fails, others still execute)
- Represent facts about what happened
"""

import logging
from typing import Callable, Dict, List, Type, Union
from collections import defaultdict

from ..domain.commands.base import Command
from ..domain.events.base import Event


logger = logging.getLogger(__name__)


Message = Union[Command, Event]


class MessageBus:
    """
    Central message bus for routing commands and events.

    Implements the Mediator pattern to decouple message producers from consumers.
    """

    def __init__(self):
        # Command handlers: command_type -> handler function
        self._command_handlers: Dict[Type[Command], Callable] = {}

        # Event handlers: event_type -> list of handler functions
        self._event_handlers: Dict[Type[Event], List[Callable]] = defaultdict(list)

        # Message queue for processing
        self._queue: List[Message] = []

    def register_command_handler(
        self,
        command_type: Type[Command],
        handler: Callable
    ) -> None:
        """
        Register a handler for a command type.

        A command can have only one handler.
        """
        if command_type in self._command_handlers:
            raise ValueError(
                f"Command {command_type.__name__} already has a handler registered"
            )
        self._command_handlers[command_type] = handler
        logger.debug(f"Registered command handler for {command_type.__name__}")

    def register_event_handler(
        self,
        event_type: Type[Event],
        handler: Callable
    ) -> None:
        """
        Register a handler for an event type.

        An event can have multiple handlers.
        """
        self._event_handlers[event_type].append(handler)
        logger.debug(
            f"Registered event handler for {event_type.__name__} "
            f"(total handlers: {len(self._event_handlers[event_type])})"
        )

    def handle(self, message: Message) -> None:
        """
        Handle a message (command or event).

        Commands are handled immediately by their single handler.
        Events are queued and processed in order.
        """
        self._queue = [message]
        while self._queue:
            message = self._queue.pop(0)

            if isinstance(message, Command):
                self._handle_command(message)
            elif isinstance(message, Event):
                self._handle_event(message)
            else:
                raise ValueError(f"Unknown message type: {type(message)}")

    def _handle_command(self, command: Command) -> None:
        """Handle a command by routing to its handler"""
        logger.debug(f"Handling command: {command.command_type}")

        handler = self._command_handlers.get(type(command))
        if not handler:
            raise ValueError(
                f"No handler registered for command {command.command_type}"
            )

        try:
            # Execute command handler
            # Handler may return events that should be published
            result = handler(command)

            # If handler returns events, add them to queue
            if result:
                if isinstance(result, list):
                    self._queue.extend(result)
                elif isinstance(result, Event):
                    self._queue.append(result)

        except Exception as e:
            logger.error(
                f"Error handling command {command.command_type}: {str(e)}",
                exc_info=True
            )
            raise

    def _handle_event(self, event: Event) -> None:
        """Handle an event by routing to all its handlers"""
        logger.debug(f"Handling event: {event.event_type}")

        handlers = self._event_handlers.get(type(event), [])

        if not handlers:
            logger.debug(f"No handlers registered for event {event.event_type}")
            return

        for handler in handlers:
            try:
                # Execute event handler
                # Handler may return more events
                result = handler(event)

                # If handler returns events, add them to queue
                if result:
                    if isinstance(result, list):
                        self._queue.extend(result)
                    elif isinstance(result, Event):
                        self._queue.append(result)

            except Exception as e:
                # Event handlers should not fail the entire process
                # Log and continue with other handlers
                logger.error(
                    f"Error in event handler for {event.event_type}: {str(e)}",
                    exc_info=True
                )
                continue

    def publish(self, event: Event) -> None:
        """
        Publish an event to all registered handlers.

        This is an alias for handle() for semantic clarity.
        """
        self.handle(event)

    def publish_all(self, events: List[Event]) -> None:
        """Publish multiple events"""
        for event in events:
            self.publish(event)

    def clear_handlers(self) -> None:
        """Clear all registered handlers (useful for testing)"""
        self._command_handlers.clear()
        self._event_handlers.clear()
        logger.debug("Cleared all message handlers")

    def get_command_handler(self, command_type: Type[Command]) -> Callable:
        """Get the handler for a command type"""
        return self._command_handlers.get(command_type)

    def get_event_handlers(self, event_type: Type[Event]) -> List[Callable]:
        """Get all handlers for an event type"""
        return self._event_handlers.get(event_type, [])


# Global message bus instance
_message_bus: MessageBus = None


def get_message_bus() -> MessageBus:
    """Get the global message bus instance"""
    global _message_bus
    if _message_bus is None:
        _message_bus = MessageBus()
    return _message_bus


def reset_message_bus() -> None:
    """Reset the global message bus (useful for testing)"""
    global _message_bus
    _message_bus = MessageBus()
