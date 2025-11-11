# Professional Trading Framework

A robust, event-driven trading framework built with enterprise architectural patterns from "Architecture Patterns with Python" by Harry Percival & Bob Gregory. Supports multiple brokers, asset classes, and comprehensive backtesting.

## 🎯 Features

### Core Architecture
- **Event-Driven Architecture**: Decoupled components communicating via events and commands
- **Domain-Driven Design**: Rich domain models with business logic
- **Repository Pattern**: Abstract data access layer
- **Unit of Work Pattern**: Transaction management
- **Message Bus**: Central event/command routing
- **CQRS**: Command Query Responsibility Segregation
- **Risk Management**: Comprehensive pre-trade risk validation

### Multi-Broker Support
- **Interactive Brokers**: Forex, stocks, futures, options
- **Binance**: Cryptocurrency spot, futures, margin
- **Alpaca**: US stocks commission-free
- **Coinbase**: Cryptocurrency trading
- **MetaTrader 5**: Forex and CFDs (Windows)

### Multi-Asset Support
- Forex (FX)
- Cryptocurrencies
- Stocks
- Futures
- Indices
- Options
- CFDs

### Backtesting
- **Dual Mode**: Historical and real-time simulation
- **Multiple Data Sources**:
  - CSV files (OHLCV)
  - PostgreSQL (tick data)
  - Yahoo Finance API
  - Custom data providers
- **Comprehensive Metrics**:
  - Returns, Sharpe ratio, drawdown
  - Win rate, profit factor
  - Equity curves
- **Event-Driven Execution**: Realistic order handling

### Risk Management
- **Position Sizing Limits**: Maximum position size as % of portfolio
- **Leverage Control**: Maximum leverage enforcement
- **Circuit Breakers**: Daily loss limits that halt trading
- **Portfolio Limits**: Maximum number of open positions
- **Concentration Limits**: Sector and asset type diversification
- **Capital Requirements**: Minimum equity and reserve cash
- **Portfolio Heat**: Total risk exposure monitoring
- **Pre-Trade Validation**: All orders validated before execution
- **Risk Violations Tracking**: Comprehensive violation logging

### Notifications & Alerts
- **Multi-Channel Support**: Email, Telegram, Slack, Discord, Webhooks
- **Real-Time Alerts**: Trade executions, order rejections, position closes
- **Customizable Filters**: Filter by level, tags, or custom rules
- **Rich Formatting**: HTML emails, formatted Telegram/Slack messages
- **Event-Driven**: Automatic notifications based on trading events
- **Flexible Configuration**: Enable/disable channels independently
- **Notification History**: Track all sent notifications

## 📁 Project Structure

```
trading_framework/
├── trading_framework/
│   ├── domain/                 # Business logic
│   │   ├── model/             # Domain entities
│   │   │   ├── asset.py       # Asset definitions
│   │   │   ├── order.py       # Order aggregate
│   │   │   ├── position.py    # Position tracking
│   │   │   ├── account.py     # Account management
│   │   │   ├── bar.py         # OHLCV bars
│   │   │   └── tick.py        # Tick data
│   │   ├── events/            # Domain events
│   │   └── commands/          # Commands
│   │
│   ├── adapters/              # External integrations
│   │   ├── brokers/           # Broker adapters
│   │   │   ├── base.py        # Base broker interface
│   │   │   ├── simulated.py   # Backtesting broker
│   │   │   ├── interactive_brokers/
│   │   │   ├── binance/
│   │   │   ├── alpaca/
│   │   │   ├── coinbase/
│   │   │   └── metatrader/
│   │   ├── data_sources/      # Data providers
│   │   │   ├── csv/
│   │   │   ├── postgresql/
│   │   │   ├── yahoo_finance/
│   │   │   └── simulator/
│   │   └── repository/        # Data persistence
│   │
│   ├── service_layer/         # Application services
│   │   ├── messagebus.py      # Event/command routing
│   │   ├── unit_of_work/      # Transaction management
│   │   └── handlers/          # Command/event handlers
│   │
│   ├── entrypoints/           # Entry points
│   │   ├── backtesting/       # Backtesting engine
│   │   ├── cli/               # Command-line interface
│   │   └── api/               # REST API
│   │
│   └── config/                # Configuration management
│
├── examples/                   # Example strategies
│   ├── strategies/
│   │   └── simple_sma_crossover.py
│   ├── run_backtest.py
│   └── configs/
│
├── tests/                      # Test suite
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── requirements.txt
├── setup.py
└── README.md
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/trading-framework.git
cd trading-framework

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Basic Usage

#### 1. Define Your Strategy

```python
from trading_framework.domain.model import Order, OrderSide, OrderType

class MyStrategy:
    def __call__(self, context):
        """Called on each bar"""
        bar = context["bar"]
        account = context["account"]

        # Your strategy logic here
        if some_buy_signal:
            order = Order(
                asset=bar.asset,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=100,
            )
            return [order]

        return None
```

#### 2. Run a Backtest

```python
from trading_framework.entrypoints.backtesting import BacktestEngine, BacktestConfig
from trading_framework.adapters.data_sources.csv import CSVDataSource
from trading_framework.domain.model import Asset, AssetType, BarResolution
from datetime import datetime
from decimal import Decimal

# Define asset
asset = Asset(
    symbol="AAPL",
    asset_type=AssetType.STOCK,
    exchange="NASDAQ",
    currency="USD"
)

# Configure data source
data_source = CSVDataSource({
    "data_dir": "./data",
    "filename_pattern": "{symbol}_{resolution}.csv"
})

# Configure backtest
config = BacktestConfig(
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 12, 31),
    assets=[asset],
    resolution=BarResolution.DAY_1,
    initial_capital=Decimal("100000")
)

# Create strategy
strategy = MyStrategy()

# Run backtest
engine = BacktestEngine(config, data_source, strategy)
result = await engine.run()

# Print results
result.print_summary()
```

#### 3. Live Trading (Coming Soon)

```python
from trading_framework.adapters.brokers.binance import BinanceBroker

# Configure broker
broker = BinanceBroker({
    "api_key": "your_api_key",
    "api_secret": "your_api_secret",
    "testnet": True
})

# Connect and trade
await broker.connect()
order_id = await broker.submit_order(order)
```

#### 4. Using Risk Management

```python
from trading_framework.service_layer.risk_manager import RiskManager, RiskConfig
from decimal import Decimal

# Configure risk management
risk_config = RiskConfig(
    max_position_size_pct=Decimal("0.1"),  # Max 10% per position
    max_leverage=Decimal("2.0"),           # Max 2x leverage
    max_open_positions=10,                 # Max 10 positions
    max_daily_loss_pct=Decimal("0.05"),    # 5% daily loss limit
    enforce_position_limits=True,
    enforce_leverage_limits=True,
    enforce_daily_loss_limits=True,
)

# Create risk manager
risk_manager = RiskManager(risk_config)

# Validate order before submission
is_valid, violations = risk_manager.validate_order(order, account)

if is_valid:
    await broker.submit_order(order)
else:
    for violation in violations:
        print(f"Risk violation: {violation.message}")

# Get risk metrics
metrics = risk_manager.get_risk_metrics(account)
print(f"Current leverage: {metrics['leverage']:.2f}x")
print(f"Daily P&L: ${metrics['daily_pnl']:.2f}")
```

#### 5. Setting Up Notifications

```python
from trading_framework.adapters.notifications import (
    NotificationManager,
    ConsoleNotifier,
    TelegramNotifier,
    EmailNotifier,
    SlackNotifier,
)

# Create notification manager
notification_manager = NotificationManager()

# Add console notifier (for testing)
console = ConsoleNotifier({
    "enabled": True,
    "min_level": "INFO",
    "colored": True,
})
notification_manager.add_notifier(console)

# Add Telegram notifier
telegram = TelegramNotifier({
    "enabled": True,
    "bot_token": "YOUR_BOT_TOKEN",  # From @BotFather
    "chat_ids": ["YOUR_CHAT_ID"],
    "min_level": "SUCCESS",  # Only trades and above
})
notification_manager.add_notifier(telegram)

# Add Email notifier
email = EmailNotifier({
    "enabled": True,
    "smtp_host": "smtp.gmail.com",
    "smtp_port": 587,
    "smtp_user": "your_email@gmail.com",
    "smtp_password": "your_app_password",
    "from_email": "your_email@gmail.com",
    "to_emails": ["recipient@example.com"],
    "min_level": "WARNING",  # Only important alerts
})
notification_manager.add_notifier(email)

# Use with backtest
config = BacktestConfig(
    # ... other config ...
    enable_notifications=True,
    notification_manager=notification_manager,
)

# Notifications will be sent automatically for:
# - Trade executions
# - Order rejections
# - Position closes
# - Backtest completion summary
```

## 📊 Example: SMA Crossover Strategy

```python
from collections import deque
from decimal import Decimal
from trading_framework.domain.model import Order, OrderSide, OrderType

class SMACrossover:
    def __init__(self, fast_period=10, slow_period=30):
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.price_history = {}
        self.prev_fast_sma = {}
        self.prev_slow_sma = {}

    def __call__(self, context):
        bar = context["bar"]
        account = context["account"]

        # Initialize price history
        symbol = bar.asset.full_symbol
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.slow_period)

        self.price_history[symbol].append(bar.close)

        # Calculate SMAs
        if len(self.price_history[symbol]) < self.slow_period:
            return None

        fast_sma = self._sma(symbol, self.fast_period)
        slow_sma = self._sma(symbol, self.slow_period)

        # Detect crossover
        prev_fast = self.prev_fast_sma.get(symbol)
        prev_slow = self.prev_slow_sma.get(symbol)

        self.prev_fast_sma[symbol] = fast_sma
        self.prev_slow_sma[symbol] = slow_sma

        if prev_fast and prev_slow:
            # Bullish crossover
            if prev_fast <= prev_slow and fast_sma > slow_sma:
                return [Order(
                    asset=bar.asset,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=Decimal("100")
                )]

            # Bearish crossover
            elif prev_fast >= prev_slow and fast_sma < slow_sma:
                position = account.get_position(bar.asset)
                if position and position.is_long:
                    return [Order(
                        asset=bar.asset,
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=position.quantity
                    )]

        return None

    def _sma(self, symbol, period):
        prices = list(self.price_history[symbol])[-period:]
        return sum(prices) / len(prices)
```

## 🏗️ Architecture

### Event-Driven Flow

```
Market Data → Events → Strategy → Commands → Handlers → Orders → Broker
                ↓                                           ↓
            Subscribers                               Order Events
                                                           ↓
                                                   Position Updates
```

### Key Components

1. **Domain Layer**: Pure business logic, no infrastructure dependencies
2. **Service Layer**: Orchestrates use cases using repositories and UoW
3. **Adapters**: Translate between domain and external systems
4. **Message Bus**: Routes events and commands to handlers

### Design Patterns

- **Aggregate Pattern**: Order, Position, Account are aggregates
- **Repository Pattern**: Abstract data access
- **Unit of Work**: Manage transactions
- **Event Sourcing**: Track all state changes via events
- **CQRS**: Separate read and write models

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=trading_framework --cov-report=html

# Run specific test file
pytest tests/unit/test_order.py

# Run integration tests
pytest tests/integration/
```

## 📈 Broker Integration Status

| Broker | Status | Assets | Notes |
|--------|--------|--------|-------|
| Simulated | ✅ Complete | All | For backtesting |
| Interactive Brokers | 🚧 In Progress | Stocks, Forex, Futures | Requires `ib_insync` |
| Binance | 🚧 In Progress | Crypto | REST + WebSocket |
| Alpaca | 🚧 In Progress | US Stocks | Commission-free |
| Coinbase | 📋 Planned | Crypto | Advanced Trade API |
| MetaTrader 5 | 📋 Planned | Forex, CFDs | Windows only |

## 🔧 Configuration

### YAML Configuration

```yaml
# config.yaml
broker:
  name: binance
  api_key: ${BINANCE_API_KEY}
  api_secret: ${BINANCE_API_SECRET}
  testnet: true

data_source:
  type: csv
  data_dir: ./data
  filename_pattern: "{symbol}_{resolution}.csv"

strategy:
  name: sma_crossover
  fast_period: 10
  slow_period: 30

risk_management:
  max_position_size_pct: 0.1
  max_leverage: 1.0
  max_open_positions: 10

backtest:
  start_date: 2023-01-01
  end_date: 2023-12-31
  initial_capital: 100000
```

### Loading Configuration

```python
from trading_framework.config import load_config

# Load from file
config = load_config("config.yaml")

# Or from environment variables
config = load_config()  # Reads TRADING_* env vars
```

## 📚 Documentation

- [Architecture Overview](docs/architecture.md)
- [Domain Models](docs/domain_models.md)
- [Broker Integration Guide](docs/broker_integration.md)
- [Strategy Development](docs/strategy_development.md)
- [Backtesting Guide](docs/backtesting.md)
- [API Reference](docs/api_reference.md)

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- "Architecture Patterns with Python" by Harry Percival & Bob Gregory
- Cloud Design Patterns (Microsoft Azure)
- Domain-Driven Design community

## ⚠️ Disclaimer

This software is for educational and research purposes only. Do not risk money which you are afraid to lose. USE THE SOFTWARE AT YOUR OWN RISK. THE AUTHORS AND ALL AFFILIATES ASSUME NO RESPONSIBILITY FOR YOUR TRADING RESULTS.

Always test strategies in a paper trading environment before deploying with real money.

## 📞 Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/yourusername/trading-framework/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/trading-framework/discussions)

---

Made with ❤️ by the Trading Framework Team
