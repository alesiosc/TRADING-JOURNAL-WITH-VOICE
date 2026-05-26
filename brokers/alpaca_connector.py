"""
Alpaca Broker Connector — free stocks/crypto API.

Setup:
  1. Create an Alpaca account at https://alpaca.markets
  2. Generate API keys from Dashboard > Paper Trading
  3. Set in .env: ALPACA_API_KEY, ALPACA_SECRET_KEY

Rate limits: 200 req/min (free), 1000/min (funded)
"""

from datetime import date, datetime, timezone
from typing import Optional
import logging

from brokers import BaseBrokerConnector, register_connector

logger = logging.getLogger("brokers.alpaca")


class AlpacaConnector(BaseBrokerConnector):
    """Connector for Alpaca Markets API (US stocks, crypto, options)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self._api = None
        self._initialized = False

    def _ensure_api(self):
        """Lazy-init the Alpaca SDK."""
        if self._initialized:
            return

        api_key = self.config.get("api_key") or self._get_env("ALPACA_API_KEY")
        secret_key = self.config.get("secret_key") or self._get_env("ALPACA_SECRET_KEY")
        paper = self.config.get("paper", True)
        base_url = self.config.get(
            "base_url",
            "https://paper-api.alpaca.markets" if paper else "https://api.alpaca.markets",
        )

        try:
            from alpaca.trading.client import TradingClient
            self._api = TradingClient(api_key, secret_key, paper=paper)
            self._initialized = True
            logger.info("Alpaca connector initialized (%s)", "paper" if paper else "live")
        except ImportError:
            logger.error(
                "alpaca-py not installed. Run: pip install alpaca-py"
            )
            raise
        except Exception as e:
            logger.error("Failed to initialize Alpaca: %s", e)
            raise

    def _get_env(self, key: str) -> str:
        """Get from environment."""
        import os
        return os.environ.get(key, "")

    def fetch_trades(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[dict]:
        """Fetch closed trades from Alpaca."""
        self._ensure_api()

        # Default: last 90 days
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            from datetime import timedelta
            start_date = end_date - timedelta(days=90)

        try:
            from alpaca.trading.requests import GetActivitiesRequest
            from alpaca.trading.enums import ActivityType

            request = GetActivitiesRequest(
                activity_type=ActivityType.FILL,
                after=start_date.isoformat(),
                until=end_date.isoformat(),
                page_size=100,
            )

            activities = self._api.get_activities(request)
            trades = []
            for act in activities:
                trade = {
                    "broker_trade_id": act.id or act.activity_id or "",
                    "broker": "alpaca",
                    "instrument": act.symbol or "",
                    "direction": "long" if act.side == "buy" else "short",
                    "volume": abs(float(act.qty or 0)),
                    "entry_price": float(act.price or 0),
                    "exit_price": None,
                    "entry_time": act.activity_datetime.isoformat() if hasattr(act, "activity_datetime") and act.activity_datetime else None,
                    "exit_time": None,
                    "pnl": float(act.net_amount or 0),
                    "pnl_pct": None,
                    "commission": float(act.commission or act.orig_commission or 0),
                    "swap": 0.0,
                    "status": "closed",
                    "strategy_tag": "",
                    "notes": "",
                }
                trades.append(trade)

            logger.info("Fetched %d trades from Alpaca", len(trades))
            return trades

        except Exception as e:
            logger.error("Alpaca fetch_trades failed: %s", e)
            return []

    def fetch_positions(self) -> list[dict]:
        """Fetch current open positions."""
        self._ensure_api()
        try:
            positions = self._api.get_all_positions()
            result = []
            for pos in positions:
                result.append({
                    "instrument": pos.symbol,
                    "direction": "long" if float(pos.qty) > 0 else "short",
                    "volume": abs(float(pos.qty)),
                    "entry_price": float(pos.avg_entry_price),
                    "current_price": float(pos.current_price),
                    "pnl_unrealized": float(pos.unrealized_pl),
                    "pnl_pct": float(pos.unrealized_plpc),
                })
            return result
        except Exception as e:
            logger.error("Alpaca fetch_positions failed: %s", e)
            return []

    def get_account_summary(self) -> dict:
        """Fetch account summary."""
        self._ensure_api()
        try:
            account = self._api.get_account()
            return {
                "broker": "alpaca",
                "balance": float(account.cash),
                "equity": float(account.equity),
                "buying_power": float(account.buying_power),
                "day_trade_count": int(account.daytrade_count),
                "status": account.status,
            }
        except Exception as e:
            logger.error("Alpaca get_account_summary failed: %s", e)
            return {}


# Register this connector
register_connector("alpaca", AlpacaConnector)
