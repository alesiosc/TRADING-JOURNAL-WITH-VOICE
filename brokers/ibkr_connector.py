"""
Interactive Brokers Connector (via ib_insync).

Setup:
  1. Install TWS or IB Gateway from https://www.interactivebrokers.com
  2. Enable API connections: Edit > Global Configuration > API > Settings
  3. Set port: TWS paper=7497, TWS live=7496, Gateway paper=4002, Gateway live=4001
  4. Uncheck "Use Master Client ID" if needed

Requires TWS/IB Gateway running before connecting.

This connector groups execution fills by order ID to reconstruct
complete trades with proper volume aggregation.
"""

from datetime import date, datetime, timezone, timedelta
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
        self._host = self.config.get("host") or self._get_env("IBKR_HOST") or "127.0.0.1"
        self._port = int(
            self.config.get("port") or self._get_env("IBKR_PORT") or "7497"
        )
        self._client_id = int(self.config.get("client_id") or "1")

    def _get_env(self, key: str) -> str:
        import os
        return os.environ.get(key, "")

    def connect(self) -> bool:
        """Connect to TWS/IB Gateway."""
        if self._connected:
            return True

        try:
            from ib_insync import IB
            self._ib = IB()
            self._ib.connect(self._host, self._port, clientId=self._client_id)
            self._connected = True
            logger.info(
                "IBKR connected to %s:%s (client ID %d)",
                self._host, self._port, self._client_id,
            )
            return True

        except ConnectionRefusedError:
            logger.error(
                "Cannot connect to TWS/IB Gateway at %s:%s. "
                "Is it running with API enabled?",
                self._host, self._port,
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
            self._ib = None

    def fetch_trades(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> list[dict]:
        """
        Fetch trade executions from IBKR.

        Groups fills by permId (order permanent ID) to reconstruct
        complete trades. Each fill has: execId, time, side, shares, price,
        commission, cumQty, permId, orderRef, contract.
        """
        if not self.connect():
            return []

        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=90)

        try:
            start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
            end_dt = datetime.combine(end_date, datetime.max.time(), tzinfo=timezone.utc)

            # Fetch fills (executions)
            fills = self._ib.fills()
            trades = []

            # Group fills by permId (order permanent ID)
            fill_groups: dict[int, list] = {}
            for fill in fills:
                exec_data = fill.execution
                perm_id = exec_data.permId
                if perm_id not in fill_groups:
                    fill_groups[perm_id] = []
                fill_groups[perm_id].append(fill)

            for perm_id, group in fill_groups.items():
                # Sort by time
                group.sort(key=lambda f: f.execution.time or datetime.min.replace(tzinfo=timezone.utc))

                first_fill = group[0]
                last_fill = group[-1]
                first_exec = first_fill.execution
                last_exec = last_fill.execution
                contract = first_fill.contract

                ts = first_exec.time
                if ts and ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)

                # Apply date filter based on first fill time
                if ts and (ts < start_dt or ts > end_dt):
                    continue

                exit_ts = last_exec.time
                if exit_ts and exit_ts.tzinfo is None:
                    exit_ts = exit_ts.replace(tzinfo=timezone.utc)

                # Aggregate across fills
                total_shares = sum(float(f.execution.shares) for f in group)
                avg_price = sum(
                    float(f.execution.price) * float(f.execution.shares) for f in group
                ) / total_shares if total_shares > 0 else 0
                total_commission = sum(float(f.execution.commission or 0) for f in group)

                # Determine direction from first fill side
                side = first_exec.side or ""
                direction = "long" if side.upper() == "BOT" else "short"

                # IBKR fills don't include PnL directly at execution level
                # We can compute estimated PnL if we knew cost basis, but we don't
                # from fills alone. For realized PnL we'd need to match buys/sells
                # by contract. Return None and let the sync logic compute it.
                trade = {
                    "broker_trade_id": str(perm_id),
                    "broker": "ibkr",
                    "instrument": (
                        contract.localSymbol
                        or contract.symbol
                        or ""
                    ),
                    "direction": direction,
                    "volume": total_shares,
                    "entry_price": round(avg_price, 6),
                    "exit_price": None,
                    "entry_time": ts.isoformat() if ts else None,
                    "exit_time": exit_ts.isoformat() if exit_ts else None,
                    "pnl": None,  # Not available from fill data
                    "pnl_pct": None,
                    "commission": round(total_commission, 4),
                    "swap": 0.0,
                    "status": "closed",
                    "strategy_tag": first_exec.orderRef or "",
                    "notes": "",
                }
                trades.append(trade)

            logger.info(
                "Fetched %d trades from IBKR (%d fill groups from %d fills)",
                len(trades), len(fill_groups), len(fills),
            )
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
                    "current_price": float(pos.marketPrice) if hasattr(pos, "marketPrice") and pos.marketPrice else None,
                    "pnl_unrealized": float(pos.unrealizedPNL) if hasattr(pos, "unrealizedPNL") and pos.unrealizedPNL else None,
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

    def check_connection(self) -> dict:
        """Check if IBKR is connected and reachable."""
        if not self.connect():
            return {"connected": False, "error": "Could not connect to TWS/IB Gateway"}
        try:
            # If connected, try to fetch account info as a ping
            self._ib.reqCurrentTime()
            return {
                "connected": True,
                "host": self._host,
                "port": self._port,
            }
        except Exception as e:
            self._connected = False
            return {"connected": False, "error": str(e)}


register_connector("ibkr", IBKRConnector)
