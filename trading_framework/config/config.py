"""
Configuration Management

Supports loading configuration from:
- YAML files
- JSON files
- Environment variables
- Python dictionaries
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Main configuration class"""

    # Broker configuration
    broker: Dict[str, Any] = field(default_factory=dict)

    # Data source configuration
    data_source: Dict[str, Any] = field(default_factory=dict)

    # Strategy configuration
    strategy: Dict[str, Any] = field(default_factory=dict)

    # Risk management
    risk_management: Dict[str, Any] = field(default_factory=dict)

    # Backtesting
    backtest: Dict[str, Any] = field(default_factory=dict)

    # Logging
    logging: Dict[str, Any] = field(default_factory=dict)

    # Database
    database: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Set defaults"""
        # Default risk management
        if not self.risk_management:
            self.risk_management = {
                "max_position_size_pct": 0.1,
                "max_leverage": 1.0,
                "max_open_positions": 10,
            }

        # Default logging
        if not self.logging:
            self.logging = {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "Config":
        """Create Config from dictionary"""
        return cls(
            broker=config_dict.get("broker", {}),
            data_source=config_dict.get("data_source", {}),
            strategy=config_dict.get("strategy", {}),
            risk_management=config_dict.get("risk_management", {}),
            backtest=config_dict.get("backtest", {}),
            logging=config_dict.get("logging", {}),
            database=config_dict.get("database", {}),
        )

    @classmethod
    def from_json(cls, filepath: str) -> "Config":
        """Load configuration from JSON file"""
        with open(filepath, 'r') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)

    @classmethod
    def from_yaml(cls, filepath: str) -> "Config":
        """Load configuration from YAML file"""
        try:
            import yaml
            with open(filepath, 'r') as f:
                config_dict = yaml.safe_load(f)
            return cls.from_dict(config_dict)
        except ImportError:
            raise ImportError("PyYAML is required for YAML configuration. Install with: pip install pyyaml")

    @classmethod
    def from_env(cls, prefix: str = "TRADING_") -> "Config":
        """
        Load configuration from environment variables.

        Example:
            TRADING_BROKER_NAME=binance
            TRADING_BROKER_API_KEY=xxx
        """
        config_dict = {}

        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and convert to nested dict
                key_parts = key[len(prefix):].lower().split('_')

                # Navigate/create nested structure
                current = config_dict
                for part in key_parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]

                # Set value
                current[key_parts[-1]] = value

        return cls.from_dict(config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "broker": self.broker,
            "data_source": self.data_source,
            "strategy": self.strategy,
            "risk_management": self.risk_management,
            "backtest": self.backtest,
            "logging": self.logging,
            "database": self.database,
        }

    def to_json(self, filepath: str) -> None:
        """Save configuration to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    def to_yaml(self, filepath: str) -> None:
        """Save configuration to YAML file"""
        try:
            import yaml
            with open(filepath, 'w') as f:
                yaml.dump(self.to_dict(), f, default_flow_style=False)
        except ImportError:
            raise ImportError("PyYAML is required. Install with: pip install pyyaml")


def load_config(filepath: Optional[str] = None) -> Config:
    """
    Load configuration from file or environment.

    Args:
        filepath: Path to config file (JSON or YAML)

    Returns:
        Config object
    """
    if filepath:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")

        if path.suffix in ['.yaml', '.yml']:
            return Config.from_yaml(filepath)
        elif path.suffix == '.json':
            return Config.from_json(filepath)
        else:
            raise ValueError(f"Unsupported config file format: {path.suffix}")
    else:
        # Try to load from environment
        return Config.from_env()
