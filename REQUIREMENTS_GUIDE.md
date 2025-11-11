# Requirements Installation Guide

This project provides multiple requirements files for different use cases:

## 📦 Available Requirements Files

### 1. `requirements.txt` - Full Installation (Recommended)
Complete installation with all features and broker support.

```bash
pip install -r requirements.txt
```

**Includes:**
- Core framework dependencies
- All broker adapters (IB, Binance, Alpaca, MetaTrader, Coinbase)
- Data sources (Yahoo Finance, PostgreSQL)
- Notification system (Email, Telegram, Slack, Webhooks)
- Performance monitoring and logging
- Visualization tools (matplotlib, plotly, seaborn)
- Web framework for API/UI (FastAPI)

**Use this if:** You want the complete trading framework with all capabilities.

---

### 2. `requirements-minimal.txt` - Core Only
Minimal installation with just the essential framework.

```bash
pip install -r requirements-minimal.txt
```

**Includes:**
- Core framework dependencies
- Data handling (pandas, numpy)
- Configuration management
- Notification system
- Basic monitoring

**Excludes:**
- Broker-specific libraries
- Database drivers (PostgreSQL)
- Visualization libraries
- Web framework

**Use this if:** You're building a custom implementation or only need specific brokers.

After minimal install, add brokers individually:
```bash
# Interactive Brokers
pip install ib-insync>=0.9.86

# Binance
pip install python-binance>=1.0.17

# Alpaca
pip install alpaca-trade-api>=3.0.0

# MetaTrader 5 (Windows only)
pip install MetaTrader5>=5.0.45

# Coinbase
pip install cbpro>=1.1.4
```

---

### 3. `requirements-dev.txt` - Development Environment
Full installation plus development tools.

```bash
pip install -r requirements-dev.txt
```

**Includes:**
- Everything from `requirements.txt`
- Testing frameworks (pytest, pytest-asyncio, pytest-cov)
- Code quality tools (black, flake8, mypy, pylint)
- Documentation tools (sphinx)
- Debugging tools (ipython, ipdb)

**Use this if:** You're developing or contributing to the framework.

---

## 🚀 Quick Start

### For Regular Users:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install full framework
pip install -r requirements.txt
```

### For Developers:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install with dev tools
pip install -r requirements-dev.txt
```

### For Minimal Setup:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install minimal framework
pip install -r requirements-minimal.txt

# Add specific broker (example: Binance)
pip install python-binance
```

---

## 📋 Dependency Categories

### Core Dependencies
- `python-dateutil` - Date/time utilities
- `pytz` - Timezone handling
- `pandas` - Data analysis
- `numpy` - Numerical computing

### Configuration
- `pyyaml` - YAML configuration files
- `python-dotenv` - Environment variable management

### Broker APIs
- `ib-insync` - Interactive Brokers
- `python-binance` - Binance cryptocurrency exchange
- `alpaca-trade-api` - Alpaca stock trading
- `MetaTrader5` - MetaTrader 5 (Forex/CFDs, Windows only)
- `cbpro` - Coinbase Pro

### Data Sources
- `yfinance` - Yahoo Finance market data
- `psycopg2-binary` - PostgreSQL database
- `sqlalchemy` - Database ORM

### Notifications
- `aiohttp` - Async HTTP (for Telegram, Slack, webhooks)
- `colorama` - Colored console output
- Email uses built-in `smtplib` (no extra dependency)

### Performance & Monitoring
- `tqdm` - Progress bars
- `loguru` - Advanced logging

### Visualization (Optional)
- `matplotlib` - Plotting library
- `plotly` - Interactive charts
- `seaborn` - Statistical visualization

### Web Framework (Optional)
- `fastapi` - Modern web framework for API
- `uvicorn` - ASGI server

---

## 🔧 Platform-Specific Notes

### Windows Users
MetaTrader5 is only available on Windows:
```bash
pip install MetaTrader5>=5.0.45
```

### Linux/Mac Users
MetaTrader5 will be skipped automatically due to platform requirements.

---

## ⚙️ Environment Variables

Create a `.env` file for sensitive configuration:

```env
# Broker API Keys
IB_HOST=127.0.0.1
IB_PORT=7497
IB_CLIENT_ID=1

BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_secret

ALPACA_API_KEY=your_alpaca_key
ALPACA_API_SECRET=your_alpaca_secret

# Notification Settings
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Database
DATABASE_URL=postgresql://user:password@localhost/trading_db
```

---

## 🧪 Verifying Installation

After installation, verify everything works:

```python
# Test core framework
from trading_framework.domain.model import Asset, AssetType, Order
print("✅ Core framework imported successfully")

# Test notifications
from trading_framework.adapters.notifications import NotificationManager
print("✅ Notification system imported successfully")

# Test backtesting
from trading_framework.entrypoints.backtesting import BacktestEngine
print("✅ Backtesting engine imported successfully")
```

---

## 📚 Additional Resources

- See `README.md` for framework overview
- See `ARCHITECTURE.md` for technical architecture
- See `examples/` directory for usage examples

