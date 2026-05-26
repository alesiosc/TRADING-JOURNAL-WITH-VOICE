"""
Interactive Brokers Connector (via ib_insync).

Setup:
  1. Install TWS or IB Gateway from https://www.interactivebrokers.com
  2. Enable API connections: Edit > Global Configuration > API > Settings
  3. Set port: TWS paper=7497, TWS live=7496, Gateway paper=4002, Gateway live=4001
  4. Uncheck "Use Master Client ID" if needed

Requires TWS/IB Gateway running before connecting.
"""

from datetime import date, datetime, timezone
from typing import Optional
import logging

from brokers import BaseBrokerConnector, register_connector

logger = logging.getLogger("brokers.ibkr")


class IBKRConnector(BaseBrokerConnector):
    """Connector for Interactive Brokers via ib_insync."""

    def __init__(self, config: dict):
        super().__init__(config)
        self._ib = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to TWS/IB Gateway."""
        if self._connected:
            return True

        try:
            from ib_insync import IB
            self._ib = IB()

            host = self.config.get("host", "127.0.0.1")
            port = self.config.get("port", 7497)
            client_id = self.config.get("client_id", 1)

            self._ib.connect(host, port, clientId=client_id)
            self._connected = True
            logger.info("IBKR connected to %s:%s (client ID %d)", host, port, client_id)
            return True

        except ConnectionRefusedError:
            logger.error(
                "Cannot connect to TWS/IB Gateway at %s:%s. "
                "Is it running with API enabled?",
                host, port,
            )
            return False
        except ImportError:
            logger.error("ib_insync not installed. Run: pip install ib_insync")
            return False
        except Exception as e:
            logger.error("IBKR connection failed: %s", e)
            return False

    def disconnect(self):
        """Disconnect from TWS/IB Gateway."""
        if self._ib and self._connected:
            try:
                self._ib.disconnect()
            except Exception:
                pass
            self._connected = False

    def fetch_trades(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[dict]:
        """Fetch trade executions from IBKR."""
        if not self.connect():
            return []

        from datetime import timedelta
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=90)

        try:
            from ib_insync import Trade as IBTrade

            start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
            end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

            # Fetch fills (executions)
            fills = self._ib.fills()
            trades = []

            for fill in fills:
                exec_data = fill.execution
                contract = fill.contract
                ts = exec_data.time

                # Convert IB time to UTC
                if ts and ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)

                if ts and (ts < start_dt or ts > end_dt):
                    continue

                trade = {
                    "broker_trade_id": exec_data.execId or "",
                    "broker": "ibkr",
                    "instrument": contract.localSymbol or contract.symbol or "",
                    "direction": "long" if exec_data.side == "BOT" else "short",
                    "volume": float(exec_data.shares),
                    "entry_price": float(exec_data.price),
                    "exit_price": None,
                    "entry_time": ts.isoformat() if ts else None,
                    "exit_time": None,
                    "pnl": float(exec_data.cumQty) if hasattr(exec_data, "cumQty") else None,
                    "pnl_pct": None,
                    "commission": float(exec_data.commission or 0),
                    "swap": 0.0,
                    "status": "closed",
                    "strategy_tag": "",
                    "notes": "",
                }
                trades.append(trade)

            logger.info("Fetched %d trades from IBKR", len(trades))
            return trades

        except Exception as e:
            logger.error("IBKR fetch_trades failed: %s", e)
            return []

    def fetch_positions(self) -> list[dict]:
        """Fetch current positions from IBKR."""
        if not self.connect():
            return []

        try:
            positions = self._ib.positions()
            result = []
            for pos in positions:
                result.append({
                    "instrument": pos.contract.localSymbol or pos.contract.symbol,
                    "direction": "long" if float(pos.position) > 0 else "short",
                    "volume": abs(float(pos.position)),
                    "entry_price": float(pos.avgCost),
                    "current_price": float(pos.marketPrice) if hasattr(pos, "marketPrice") else None,
                    "pnl_unrealized": float(pos.unrealizedPNL) if hasattr(pos, "unrealizedPNL") else None,
                })
            return result
        except Exception as e:
            logger.error("IBKR fetch_positions failed: %s", e)
            return []

    def get_account_summary(self) -> dict:
        """Fetch account summary from IBKR."""
        if not self.connect():
            return {}

        try:
            summary = {}
            for tag in ("TotalCashBalance", "NetLiquidation", "BuyingPower", "GrossPositionValue"):
                values = self._ib.accountSummary(tag)
                if values:
                    summary[tag] = float(values[0].value)
            return {
                "broker": "ibkr",
                **summary,
            }
        except Exception as e:
            logger.error("IBKR get_account_summary failed: %s", e)
            return {}


register_connector("ibkr", IBKRConnector)
