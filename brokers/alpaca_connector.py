"""
Alpaca Broker Connector — free stocks/crypto API.

Setup:
  1. Create an Alpaca account at https://alpaca.markets
  2. Generate API keys from Dashboard > Paper Trading
  3. Set in .env: ALPACA_API_KEY, ALPACA_SECRET_KEY

Rate limits: 200 req/min (free), 1000/min (funded)

This connector groups fills by order_id to reconstruct complete trades
with entry and (where available) exit legs.
"""

from datetime import date, datetime, timezone, timedelta
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

        if not api_key or not secret_key:
            logger.warning(
                "Alpaca API keys not configured. "
                "Set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env"
            )
            return

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
        import os
        return os.environ.get(key, "")

    def fetch_trades(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[dict]:
        """
        Fetch closed trades from Alpaca.

        Groups fill activities by order_id to reconstruct complete trades.
        Returns normalized dicts per the canonical schema.
        """
        self._ensure_api()
        if not self._api:
            logger.warning("Alpaca not configured, returning empty trades")
            return []

        # Default: last 90 days
        if end_date is None:
            end_date = date.today()
        if start_date is None:
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

            # Group fills by order_id to reconstruct complete trades
            fill_groups: dict[str, list] = {}
            for act in activities:
                order_id = getattr(act, "order_id", None) or act.id or act.activity_id or ""
                if order_id not in fill_groups:
                    fill_groups[order_id] = []
                fill_groups[order_id].append(act)

            trades = []
            for order_id, fills in fill_groups.items():
                # Sort fills by time
                fills.sort(key=lambda f: getattr(f, "activity_datetime", None) or "")

                total_qty = sum(abs(float(f.qty or 0)) for f in fills)
                avg_price = sum(float(f.price or 0) * abs(float(f.qty or 0)) for f in fills) / total_qty if total_qty > 0 else 0
                total_commission = sum(float(f.commission or f.orig_commission or 0) for f in fills)
                total_pnl = sum(float(f.net_amount or 0) for f in fills)

                first_fill = fills[0]
                last_fill = fills[-1]

                side = getattr(first_fill, "side", "") or ""
                direction = "long" if side.lower() == "buy" else "short"

                entry_time = None
                if hasattr(first_fill, "activity_datetime") and first_fill.activity_datetime:
                    if isinstance(first_fill.activity_datetime, str):
                        entry_time = first_fill.activity_datetime
                    else:
                        entry_time = first_fill.activity_datetime.isoformat()

                exit_time = None
                if hasattr(last_fill, "activity_datetime") and last_fill.activity_datetime:
                    if isinstance(last_fill.activity_datetime, str):
                        exit_time = last_fill.activity_datetime
                    else:
                        exit_time = last_fill.activity_datetime.isoformat()

                trade = {
                    "broker_trade_id": str(order_id),
                    "broker": "alpaca",
                    "instrument": (getattr(first_fill, "symbol", "") or ""),
                    "direction": direction,
                    "volume": total_qty,
                    "entry_price": round(avg_price, 6),
                    "exit_price": None,
                    "entry_time": entry_time,
                    "exit_time": exit_time,
                    "pnl": round(total_pnl, 4),
                    "pnl_pct": None,
                    "commission": round(total_commission, 4),
                    "swap": 0.0,
                    "status": "closed",
                    "strategy_tag": "",
                    "notes": "",
                }
                trades.append(trade)

            logger.info("Fetched %d trades from Alpaca (%d fill groups)", len(trades), len(fill_groups))
            return trades

        except Exception as e:
            logger.error("Alpaca fetch_trades failed: %s", e)
            return []

    def fetch_positions(self) -> list[dict]:
        """Fetch current open positions."""
        self._ensure_api()
        if not self._api:
            return []
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
        if not self._api:
            return {}
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

    def check_connection(self) -> dict:
        """Check if Alpaca is configured and reachable."""
        self._ensure_api()
        if not self._api:
            return {"connected": False, "error": "API keys not configured"}
        try:
            account = self._api.get_account()
            return {
                "connected": True,
                "paper": self.config.get("paper", True),
                "account_id": getattr(account, "id", ""),
                "status": getattr(account, "status", ""),
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}


# Register this connector
register_connector("alpaca", AlpacaConnector)
