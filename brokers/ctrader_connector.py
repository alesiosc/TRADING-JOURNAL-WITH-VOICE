"""
cTrader Broker Connector — best free forex/CFD API.

Setup:
  1. Register at https://connect.spotware.com
  2. Create an application to get Client ID (Public)
  3. Set in .env: CTRADER_CLIENT_ID, CTRADER_CLIENT_SECRET

Free OAuth access via Spotware's Open API.
"""

from datetime import date, datetime, timezone
from typing import Optional
import logging

from brokers import BaseBrokerConnector, register_connector

logger = logging.getLogger("brokers.ctrader")


class CTraderConnector(BaseBrokerConnector):
    """Connector for cTrader Open API (Spotware)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self._client = None
        self._token = None

    def _ensure_auth(self) -> bool:
        """Authenticate with cTrader API."""
        if self._token:
            return True

        client_id = self.config.get("client_id") or self._get_env("CTRADER_CLIENT_ID")
        client_secret = self.config.get("client_secret") or self._get_env("CTRADER_CLIENT_SECRET")

        if not client_id:
            logger.error("cTrader client_id not configured. Set CTRADER_CLIENT_ID in .env")
            return False

        try:
            import requests

            # cTrader Open API uses OAuth 2.0 client credentials
            resp = requests.post(
                "https://openapi.ctrader.com/auth/token",
                json={
                    "grant_type": "client_credentials",
                    "client_id": client_id,
                    "client_secret": client_secret or "",
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data.get("access_token", "")
            logger.info("cTrader authenticated successfully")
            return True

        except ImportError:
            logger.error("requests not installed. Run: pip install requests")
            return False
        except Exception as e:
            logger.error("cTrader auth failed: %s", e)
            return False

    def _get_env(self, key: str) -> str:
        import os
        return os.environ.get(key, "")

    def _api_request(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """Make an authenticated request to the cTrader API."""
        if not self._ensure_auth():
            return None

        try:
            import requests
            base = f"https://openapi.ctrader.com/v2/{endpoint}"
            headers = {"Authorization": f"Bearer {self._token}"}
            resp = requests.get(base, headers=headers, params=params or {}, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error("cTrader API request '%s' failed: %s", endpoint, e)
            return None

    def fetch_trades(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[dict]:
        """Fetch closed trades from cTrader."""
        data = self._api_request("orders/history")
        if not data:
            return []

        trades = []
        for order in data.get("orders", []):
            trade = {
                "broker_trade_id": str(order.get("id", "")),
                "broker": "ctrader",
                "instrument": order.get("symbol", order.get("instrument", "")),
                "direction": "long" if order.get("side", "").lower() == "buy" else "short",
                "volume": float(order.get("volume", order.get("quantity", 0))),
                "entry_price": float(order.get("price", order.get("openPrice", 0))),
                "exit_price": float(order.get("closePrice", 0)) if order.get("closePrice") else None,
                "entry_time": order.get("createdAt", order.get("openTime", "")),
                "exit_time": order.get("closedAt", order.get("closeTime", "")),
                "pnl": float(order.get("profit", order.get("pnl", 0))),
                "pnl_pct": None,
                "commission": float(order.get("commission", 0)),
                "swap": float(order.get("swap", 0)),
                "status": "closed",
                "strategy_tag": "",
                "notes": "",
            }
            trades.append(trade)

        logger.info("Fetched %d trades from cTrader", len(trades))
        return trades

    def fetch_positions(self) -> list[dict]:
        """Fetch open positions from cTrader."""
        data = self._api_request("positions")
        if not data:
            return []

        result = []
        for pos in data.get("positions", []):
            result.append({
                "instrument": pos.get("symbol", ""),
                "direction": "long" if pos.get("side", "").lower() == "buy" else "short",
                "volume": float(pos.get("volume", 0)),
                "entry_price": float(pos.get("price", 0)),
                "current_price": float(pos.get("currentPrice", 0)),
                "pnl_unrealized": float(pos.get("profit", 0)),
            })
        return result

    def get_account_summary(self) -> dict:
        """Fetch account summary from cTrader."""
        # cTrader typically requires an account ID to get details
        data = self._api_request("accounts")
        if not data:
            return {}

        accounts = data.get("accounts", [])
        if accounts:
            acc = accounts[0]
            return {
                "broker": "ctrader",
                "balance": float(acc.get("balance", 0)),
                "equity": float(acc.get("equity", 0)),
                "margin": float(acc.get("margin", 0)),
                "leverage": acc.get("leverage", ""),
            }
        return {}


register_connector("ctrader", CTraderConnector)
