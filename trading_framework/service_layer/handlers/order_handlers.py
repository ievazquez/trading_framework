"""
Order Command and Event Handlers

These handlers orchestrate order-related business logic.
They use the Unit of Work to access repositories and manage transactions.
"""

import logging
from typing import List, Optional

from ...domain.commands import SubmitOrder, CancelOrder
from ...domain.events import OrderFilled, Event
from ..unit_of_work.base import AbstractUnitOfWork
from ..risk_manager import RiskManager


logger = logging.getLogger(__name__)


def handle_submit_order(
    command: SubmitOrder,
    uow: AbstractUnitOfWork,
    risk_manager: Optional[RiskManager] = None
) -> List[Event]:
    """
    Handle SubmitOrder command.

    Validates and submits an order through the broker adapter.

    Args:
        command: SubmitOrder command
        uow: Unit of Work
        risk_manager: Optional RiskManager for validation
    """
    logger.info(f"Handling SubmitOrder command for order {command.order.order_id}")

    with uow:
        # Get the account
        account = uow.accounts.get(command.account_id)
        if not account:
            raise ValueError(f"Account {command.account_id} not found")

        order = command.order

        # Risk management validation
        if risk_manager:
            is_valid, violations = risk_manager.validate_order(order, account)

            if not is_valid:
                # Reject order due to risk violations
                violation_messages = [v.message for v in violations if v.severity == "ERROR"]
                rejection_reason = "Risk check failed: " + "; ".join(violation_messages)

                logger.warning(f"Order {order.order_id} rejected: {rejection_reason}")
                order.reject(rejection_reason)
                uow.orders.add(order)
                uow.commit()
                return uow.collect_new_events()

            # Log warnings if any
            warnings = [v for v in violations if v.severity == "WARNING"]
            if warnings:
                for warning in warnings:
                    logger.info(f"Risk warning for order {order.order_id}: {warning.message}")

        # Submit order to broker
        # In a real implementation, this would call the broker adapter
        order.submit()

        # Store order
        uow.orders.add(order)

        # Commit transaction
        uow.commit()

        # Collect and return domain events
        events = uow.collect_new_events()
        logger.info(f"Order {order.order_id} submitted successfully")
        return events


def handle_cancel_order(
    command: CancelOrder,
    uow: AbstractUnitOfWork
) -> List[Event]:
    """
    Handle CancelOrder command.

    Cancels an active order through the broker adapter.
    """
    logger.info(f"Handling CancelOrder command for order {command.order_id}")

    with uow:
        # Get the order
        order = uow.orders.get(command.order_id)
        if not order:
            raise ValueError(f"Order {command.order_id} not found")

        # Cancel order
        # In a real implementation, this would call the broker adapter
        order.cancel(command.reason)

        # Update order
        uow.orders.update(order)

        # Commit transaction
        uow.commit()

        # Collect and return domain events
        events = uow.collect_new_events()
        logger.info(f"Order {order.order_id} cancelled")
        return events


def handle_order_filled(
    event: OrderFilled,
    uow: AbstractUnitOfWork
) -> List[Event]:
    """
    Handle OrderFilled event.

    Updates positions and account balance when an order is filled.
    """
    logger.info(f"Handling OrderFilled event for order {event.order_id}")

    with uow:
        # Get the order
        order = uow.orders.get(event.order_id)
        if not order:
            logger.error(f"Order {event.order_id} not found")
            return []

        # Find the account (simplified - would need account_id on order)
        accounts = uow.accounts.list()
        if not accounts:
            logger.error("No accounts found")
            return []

        account = accounts[0]  # Simplified

        # Update or create position
        position = None
        for pos in account.positions.values():
            if pos.asset.full_symbol == event.asset.full_symbol:
                position = pos
                break

        if position is None:
            # Create new position
            from ...domain.model import Position
            position = Position(
                position_id=f"pos_{event.asset.full_symbol}_{account.account_id}",
                asset=event.asset,
                quantity=0,
                average_entry_price=event.price,
                current_price=event.price
            )
            account.positions[event.asset.full_symbol] = position

        # Update position based on order side
        from ...domain.model import OrderSide
        if event.side == OrderSide.BUY:
            position.increase_position(event.quantity, event.price)
        else:  # SELL
            if position.is_open and position.quantity >= event.quantity:
                position.reduce_position(event.quantity, event.price)
            else:
                # Opening short position or closing and reversing
                position.increase_position(-event.quantity, event.price)

        # Update account cash balance
        cost = event.quantity * event.price
        if event.side == OrderSide.BUY:
            account.update_cash(-cost, f"Order {event.order_id} filled")
        else:  # SELL
            account.update_cash(cost, f"Order {event.order_id} filled")

        # Update repositories
        uow.positions.update(position)
        uow.accounts.update(account)
        uow.orders.update(order)

        # Commit transaction
        uow.commit()

        # Collect and return new events
        events = uow.collect_new_events()
        logger.info(f"Position updated for order {event.order_id}")
        return events
