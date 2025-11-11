# Trading Framework Architecture

## Overview

This trading framework implements a professional, event-driven architecture based on principles from "Architecture Patterns with Python" and cloud design patterns. It supports multiple brokers, asset classes, and provides comprehensive backtesting capabilities.

## Architecture Layers

### 1. Domain Layer (Core Business Logic)

The domain layer contains pure business logic with no infrastructure dependencies.

#### Key Components:

**Domain Models (Aggregates)**:
- `Order`: Manages order lifecycle with state transitions and event emission
- `Position`: Tracks holdings with P&L calculations
- `Account`: Portfolio management with balance and positions
- `Asset`: Immutable value object representing tradeable instruments
- `Bar` / `Tick`: Market data value objects

**Domain Events**:
- `OrderSubmitted`, `OrderFilled`, `OrderCancelled`, `OrderRejected`
- `PositionUpdated`, `PositionClosed`
- `AccountBalanceUpdated`
- `BarReceived`, `TickReceived`

**Commands**:
- `SubmitOrder`, `CancelOrder`, `ModifyOrder`
- `UpdateAccountBalance`, `CloseAllPositions`

### 2. Service Layer (Application Logic)

Orchestrates use cases by coordinating repositories and domain logic.

#### Key Components:

**Message Bus**:
```python
MessageBus
├── Command Handlers (1:1 mapping)
│   ├── handle_submit_order()
│   ├── handle_cancel_order()
│   └── handle_modify_order()
└── Event Handlers (1:N mapping)
    ├── handle_order_filled()
    ├── handle_position_updated()
    └── handle_bar_received()
```

**Unit of Work**:
- Transaction boundary management
- Repository access
- Event collection from aggregates

**Handlers**:
- Command handlers: Execute business operations
- Event handlers: React to domain events

### 3. Adapters Layer (Infrastructure)

Connects the domain to external systems.

#### Broker Adapters:

All broker adapters implement the `AbstractBroker` interface:

```python
AbstractBroker
├── connect() / disconnect()
├── get_account() / get_positions()
├── submit_order() / cancel_order()
├── get_latest_price()
└── subscribe_bars() / subscribe_ticks()
```

Implementations:
- `SimulatedBroker`: For backtesting
- `InteractiveBrokersBroker`: TWS/Gateway integration
- `BinanceBroker`: Crypto exchange with WebSocket
- `AlpacaBroker`: US stocks commission-free
- `MetaTrader5Broker`: Forex and CFDs

#### Data Source Adapters:

All data sources implement `AbstractMarketDataRepository`:

```python
AbstractMarketDataRepository
├── get_bars(asset, resolution, start, end)
├── get_ticks(asset, start, end)
├── get_latest_bar(asset, resolution)
└── get_latest_price(asset)
```

Implementations:
- `CSVDataSource`: Read OHLCV from CSV files
- `PostgreSQLDataSource`: Tick data from database
- `YahooFinanceDataSource`: Free market data API
- `SimulatorDataSource`: Generated data

#### Repository Pattern:

```python
AbstractRepository
├── AbstractOrderRepository
│   ├── add() / get() / list()
│   └── list_active()
├── AbstractPositionRepository
│   ├── add() / get() / list()
│   └── get_by_asset()
└── AbstractAccountRepository
    ├── add() / get() / list()
    └── update()
```

### 4. Entrypoints Layer

User-facing interfaces for the framework.

- **Backtesting Engine**: Historical strategy testing
- **CLI**: Command-line interface
- **API**: REST API (future)
- **Web UI**: Dashboard (future)

## Event Flow

### 1. Backtesting Event Flow

```
CSV File → DataSource.get_bars()
    ↓
BacktestEngine loads bars
    ↓
For each bar:
    ↓
    Broker.update_price(bar.close)
    ↓
    Account.update_prices()
    ↓
    BarReceived event published
    ↓
    Strategy receives bar
    ↓
    Strategy returns Order(s)
    ↓
    Broker.submit_order()
    ↓
    Order state changes
    ↓
    OrderFilled event
    ↓
    handle_order_filled() updates Position
    ↓
    PositionUpdated event
    ↓
    Loop continues...
```

### 2. Live Trading Event Flow (Future)

```
Broker WebSocket → New Tick
    ↓
    TickReceived event
    ↓
    Strategy processes tick
    ↓
    Strategy issues Command
    ↓
    SubmitOrder command
    ↓
    handle_submit_order()
    ↓
    Risk checks (RiskManager)
    ↓
    Broker API call
    ↓
    OrderSubmitted event
    ↓
    Broker notification → OrderFilled
    ↓
    OrderFilled event
    ↓
    Position/Account updates
```

## Design Patterns

### 1. Aggregate Pattern

Orders, Positions, and Accounts are aggregates that:
- Maintain internal consistency
- Emit events on state changes
- Enforce business rules
- Have clear transactional boundaries

```python
order = Order(...)
order.submit()  # State transition
order.fill(qty, price)  # State transition + event
events = order.events  # Collect emitted events
```

### 2. Repository Pattern

Abstracts data persistence:

```python
# Domain doesn't care about storage
orders_repo.add(order)
order = orders_repo.get(order_id)
active_orders = orders_repo.list_active()
```

### 3. Unit of Work Pattern

Manages transactions and event collection:

```python
with uow:
    order = uow.orders.get(order_id)
    order.fill(qty, price)
    uow.orders.update(order)
    uow.commit()
    events = uow.collect_new_events()
    message_bus.publish_all(events)
```

### 4. Message Bus (Mediator)

Decouples components via messages:

```python
# Register handlers
message_bus.register_command_handler(SubmitOrder, handle_submit_order)
message_bus.register_event_handler(OrderFilled, handle_order_filled)

# Dispatch messages
message_bus.handle(SubmitOrder(order=order))
```

### 5. Strategy Pattern

Strategies are pluggable:

```python
class MyStrategy:
    def __call__(self, context):
        # Strategy logic
        return orders

engine = BacktestEngine(config, data_source, MyStrategy())
```

### 6. Adapter Pattern

Brokers normalized behind common interface:

```python
broker = BinanceBroker(config)
# OR
broker = InteractiveBrokersBroker(config)
# OR
broker = SimulatedBroker(config)

# Same interface for all
await broker.submit_order(order)
```

## Data Flow Architecture

### Command Flow (Write Path)

```
User/Strategy → Command → MessageBus → Handler → Aggregate → Repository → Database
                                           ↓
                                        Events
```

### Query Flow (Read Path)

```
User/Strategy → Repository → Database
                    ↓
                 Read Model
```

### Event Flow (Notifications)

```
Aggregate → Events → MessageBus → Event Handlers → Side Effects
                                        ↓
                                  More Events (cascade)
```

## Scalability Considerations

### Current Architecture (Single Process)

- In-memory repositories for backtesting
- Synchronous event handling
- Single-threaded strategy execution

### Future Enhancements

1. **Multi-Strategy Execution**:
   - Process pool for parallel strategy backtesting
   - Async event handlers

2. **Distributed Architecture**:
   - Redis/RabbitMQ for message bus
   - PostgreSQL for persistence
   - Separate services for:
     - Order management
     - Risk management
     - Market data
     - Strategy execution

3. **Event Sourcing**:
   - Store all events for replay
   - Rebuild state from event log
   - Audit trail

4. **CQRS**:
   - Separate read and write models
   - Optimized query paths
   - Materialized views

## Testing Strategy

### Unit Tests
- Domain models in isolation
- Pure business logic
- No external dependencies

### Integration Tests
- Repository implementations
- Broker adapters (with mocks)
- Message bus with handlers

### End-to-End Tests
- Full backtest scenarios
- Strategy execution
- Multi-asset portfolios

## Security Considerations

1. **API Keys**:
   - Never commit to source control
   - Use environment variables
   - Encrypt at rest

2. **Order Validation**:
   - Risk checks before submission
   - Position limits
   - Leverage limits

3. **Data Integrity**:
   - Transaction boundaries
   - Event ordering
   - Idempotent operations

## Performance Optimization

1. **Backtesting**:
   - Preload data into memory
   - Vectorized calculations where possible
   - Efficient data structures (deque for rolling windows)

2. **Live Trading**:
   - Async I/O for broker APIs
   - WebSocket connections for real-time data
   - Connection pooling for databases

3. **Memory Management**:
   - Limited history for indicators
   - Periodic cleanup of closed positions
   - Efficient bar storage

## Monitoring & Observability

1. **Logging**:
   - Structured logging (JSON)
   - Log levels per component
   - Correlation IDs for events

2. **Metrics**:
   - Order execution latency
   - Strategy signals
   - Position P&L
   - System health

3. **Alerting**:
   - Drawdown thresholds
   - Connection failures
   - Unusual activity

## Extension Points

### Adding a New Broker

1. Implement `AbstractBroker`
2. Handle broker-specific order types
3. Normalize symbols
4. Implement WebSocket for real-time data

### Adding a New Data Source

1. Implement `AbstractMarketDataRepository`
2. Parse data format to `Bar`/`Tick` objects
3. Handle date/time conversions
4. Cache for performance

### Adding a New Strategy

1. Implement `__call__(self, context)` method
2. Return `Order` objects or `None`
3. Maintain internal state as needed
4. Use context for account/position access

## References

- "Architecture Patterns with Python" - Percival & Gregory
- "Domain-Driven Design" - Eric Evans
- "Enterprise Integration Patterns" - Hohpe & Woolf
- Cloud Design Patterns - Microsoft Azure

## Glossary

- **Aggregate**: Cluster of objects treated as a unit
- **Event**: Something that happened in the past
- **Command**: Intention to perform an action
- **Repository**: Abstraction for data access
- **Unit of Work**: Transaction boundary
- **Message Bus**: Central routing for messages
- **Adapter**: Translates between domain and infrastructure
- **Value Object**: Immutable object defined by its attributes
