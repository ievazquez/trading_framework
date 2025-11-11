"""Setup script for the Trading Framework"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="professional-trading-framework",
    version="1.0.0",
    author="Trading Framework Team",
    author_email="",
    description="Professional event-driven trading framework with multi-broker and multi-asset support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/trading-framework",
    packages=find_packages(exclude=["tests", "examples"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "python-dateutil>=2.8.2",
        "pytz>=2023.3",
        "pandas>=2.0.0",
        "numpy>=1.24.0",
        "psycopg2-binary>=2.9.5",
        "sqlalchemy>=2.0.0",
        "pyyaml>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.1.0",
            "black>=23.7.0",
            "flake8>=6.0.0",
            "mypy>=1.4.0",
        ],
        "brokers": [
            "ib-insync>=0.9.86",
            "python-binance>=1.0.17",
            "alpaca-trade-api>=3.0.0",
            "cbpro>=1.1.4",
        ],
        "data": [
            "yfinance>=0.2.28",
        ],
        "viz": [
            "matplotlib>=3.7.0",
            "plotly>=5.15.0",
            "seaborn>=0.12.0",
        ],
        "api": [
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "trading-framework=trading_framework.cli:main",
        ],
    },
)
