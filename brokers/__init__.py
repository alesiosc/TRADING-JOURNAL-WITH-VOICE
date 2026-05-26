"""
Trading Journal With Voice — Unified Broker Connector Interface

All broker connectors inherit from BaseBrokerConnector and implement:
- fetch_trades(start_date, end_date) -> list[dict]
- fetch_positions() -> list[dict]
- get_account_summary() -> dict

Usage:
    from brokers.base import get_connector
    alpaca = get_connector("alpaca")
    trades = alpaca.fetch_trades()
"""

from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import Optional
import logging

logger = logging.getLogger("brokers.base")


class BaseBrokerConnector(ABC):
    """Abstract base for all broker connectors."""

    def __init__(self, config: dict):
        self.config = config
        self._name = self.__class__.__name__

    @abstractmethod
    def fetch_trades(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[dict]:
        """
        Fetch trade history from the broker.
        Returns a list of normalized trade dicts.
        """
        ...

    @abstractmethod
    def fetch_positions(self) -> list[dict]:
        """Fetch current open positions."""
        ...

    @abstractmethod
    def get_account_summary(self) -> dict:
        """Fetch account summary (balance, equity, buying power)."""
        ...

    @property
    def name(self) -> str:
        return self._name

    def normalize_trade(self, raw: dict) -> dict:
        """
        Override in subclass to convert broker-specific format
        to the canonical schema.
        """
        return raw


# ---------------------------------------------------------------------------
# Registry of available connectors
# ---------------------------------------------------------------------------
_registry: dict[str, type[BaseBrokerConnector]] = {}


def register_connector(name: str, cls: type[BaseBrokerConnector]):
    _registry[name] = cls


def get_connector(name: str, config: Optional[dict] = None) -> Optional[BaseBrokerConnector]:
    """Get an instantiated connector by name."""
    cls = _registry.get(name)
    if cls is None:
        logger.warning("No connector registered for '%s'. Available: %s", name, list(_registry.keys()))
        return None
    return cls(config or {})


def list_connectors() -> list[str]:
    """List all registered connector names."""
    return list(_registry.keys())


# ---------------------------------------------------------------------------
# Canonical trade schema
# ---------------------------------------------------------------------------
CANONICAL_FIELDS = [
    "broker_trade_id",
    "broker",
    "instrument",
    "direction",        # "long" | "short"
    "volume",
    "entry_price",
    "exit_price",
    "entry_time",       # ISO 8601
    "exit_time",        # ISO 8601
    "pnl",
    "pnl_pct",
    "commission",
    "swap",
    "status",           # "open" | "closed"
    "strategy_tag",
    "notes",
]


def validate_canonical(trade: dict) -> list[str]:
    """Validate a trade dict against the canonical schema. Returns list of missing fields."""
    missing = []
    for field in ["broker", "instrument", "direction", "volume", "entry_price"]:
        if field not in trade or trade[field] is None:
            missing.append(field)
    return missing
