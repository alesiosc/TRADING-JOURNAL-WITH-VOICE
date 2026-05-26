"""
Charles Schwab Broker Connector (post-TDA migration).

Setup:
  1. Enroll at https://developer.schwab.com
  2. Create an app to get App Key + App Secret
  3. Set callback URL (e.g., https://127.0.0.1:8181)
  4. Set in .env: SCHWAB_APP_KEY, SCHWAB_APP_SECRET

Note: Schwab migrated from TDA in Sep 2024. New projects should prefer
Alpaca or IBKR where possible. This connector uses the new Schwab API.
"""

from datetime import date, datetime, timezone
from typing import Optional
import logging
import json

from brokers import BaseBrokerConnector, register_connector

logger = logging.getLogger("brokers.schwab")


class SchwabConnector(BaseBrokerConnector):
    """Connector for Charles Schwab API (US equities, options)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self._headers = {}
        self._token_path = self.config.get("token_file", "config/schwab_token.json")

    def _ensure_auth(self) -> bool:
        """Authenticate with Schwab API using stored token."""
        if self._headers.get("Authorization"):
            return True

        # Try to load existing token
        import os
        token = self._load_token()
        if token and self._is_token_valid(token):
            self._headers = {
                "Authorization": f"Bearer {token.get('access_token', '')}",
                "Accept": "application/json",
            }
            return True

        # Need fresh token (OAuth2 with refresh)
        try:
            import requests

            app_key = self.config.get("app_key") or os.environ.get("SCHWAB_APP_KEY", "")
            app_secret = self.config.get("app_secret") or os.environ.get("SCHWAB_APP_SECRET", "")
            refresh_token = token.get("refresh_token", "") if token else ""

            if not refresh_token:
                logger.error(
                    "No refresh token for Schwab. Initial OAuth setup required.\n"
                    "See: https://developer.schwab.com/docs"
                )
                return False

            resp = requests.post(
                "https://api.schwabapi.com/v1/oauth/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": app_key,
                    "client_secret": app_secret,
                },
                timeout=10,
            )
            resp.raise_for_status()
            new_token = resp.json()
            self._save_token(new_token)
            self._headers = {
                "Authorization": f"Bearer {new_token.get('access_token', '')}",
                "Accept": "application/json",
            }
            return True

        except Exception as e:
            logger.error("Schwab auth failed: %s", e)
            return False

    def _load_token(self) -> Optional[dict]:
        try:
            with open(self._token_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def _save_token(self, token: dict):
        import os
        os.makedirs(os.path.dirname(self._token_path), exist_ok=True)
        with open(self._token_path, "w") as f:
            json.dump(token, f, indent=2)

    def _is_token_valid(self, token: dict) -> bool:
        """Check if access token is still valid."""
        expires_at = token.get("expires_at", 0)
        return datetime.now().timestamp() < expires_at - 60  # 60s buffer

    def fetch_trades(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[dict]:
        """Fetch trade history from Schwab."""
        if not self._ensure_auth():
            return []

        try:
            import requests

            params = {}
            if start_date:
                params["startDate"] = start_date.isoformat()
            if end_date:
                params["endDate"] = end_date.isoformat()

            resp = requests.get(
                "https://api.schwabapi.com/trader/v1/accounts/orders",
                headers=self._headers,
                params=params,
                timeout=15,
            )
            resp.raise_for_status()
            orders = resp.json()

            trades = []
            for order in orders:
                for leg in order.get("orderLegCollection", []):
                    instr = leg.get("instrument", {})
                    trade = {
                        "broker_trade_id": str(order.get("orderId", "")),
                        "broker": "schwab",
                        "instrument": instr.get("symbol", ""),
                        "direction": "long" if order.get("side", "").lower() == "buy" else "short",
                        "volume": float(leg.get("orderedQuantity", 0)),
                        "entry_price": float(order.get("price", 0)),
                        "exit_price": None,
                        "entry_time": order.get("enteredTime", ""),
                        "exit_time": order.get("closeTime", "") if order.get("status") == "FILLED" else None,
                        "pnl": None,
                        "pnl_pct": None,
                        "commission": 0.0,
                        "swap": 0.0,
                        "status": "closed" if order.get("status") == "FILLED" else "open",
                        "strategy_tag": "",
                        "notes": "",
                    }
                    trades.append(trade)

            return trades

        except Exception as e:
            logger.error("Schwab fetch_trades failed: %s", e)
            return []

    def fetch_positions(self) -> list[dict]:
        """Fetch current positions from Schwab."""
        if not self._ensure_auth():
            return []

        try:
            import requests
            resp = requests.get(
                "https://api.schwabapi.com/trader/v1/accounts/positions",
                headers=self._headers,
                timeout=15,
            )
            resp.raise_for_status()
            positions_data = resp.json()

            result = []
            for pos in positions_data if isinstance(positions_data, list) else positions_data.get("positions", []):
                result.append({
                    "instrument": pos.get("instrument", {}).get("symbol", ""),
                    "direction": "long" if float(pos.get("quantity", 0)) > 0 else "short",
                    "volume": abs(float(pos.get("quantity", 0))),
                    "entry_price": float(pos.get("averagePrice", 0)),
                    "current_price": float(pos.get("currentPrice", 0)),
                    "pnl_unrealized": float(pos.get("unrealizedPnL", 0)),
                })
            return result

        except Exception as e:
            logger.error("Schwab fetch_positions failed: %s", e)
            return []

    def get_account_summary(self) -> dict:
        """Fetch account summary from Schwab."""
        if not self._ensure_auth():
            return {}

        try:
            import requests
            resp = requests.get(
                "https://api.schwabapi.com/trader/v1/accounts",
                headers=self._headers,
                timeout=15,
            )
            resp.raise_for_status()
            accounts = resp.json()

            if accounts:
                acc = accounts[0] if isinstance(accounts, list) else accounts
                if isinstance(acc, dict):
                    return {
                        "broker": "schwab",
                        "account_number": acc.get("accountNumber", ""),
                        "status": acc.get("status", ""),
                    }
            return {}
        except Exception as e:
            logger.error("Schwab get_account_summary failed: %s", e)
            return {}


register_connector("schwab", SchwabConnector)
