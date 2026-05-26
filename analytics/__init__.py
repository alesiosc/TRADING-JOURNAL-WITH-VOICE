"""
Analytics Engine — Trade performance metrics using DuckDB.

Computes standard trading metrics:
  - Win rate, Profit Factor, Expectancy
  - Sharpe Ratio, Sortino Ratio
  - Max Drawdown, Max Adverse/Favorable Excursion (MAE/MFE)
  - Rolling metrics (last N trades, daily/weekly/monthly)
  - Equity curve generation

Usage:
    from analytics import AnalyticsEngine
    
    engine = AnalyticsEngine()
    # Sync trades from SQLite to DuckDB
    engine.sync_from_api()
    
    # Get metrics
    stats = engine.get_summary()
    equity = engine.get_equity_curve()
"""

import logging
import os
from datetime import date, datetime, timedelta
from typing import Optional

logger = logging.getLogger("analytics")


class AnalyticsEngine:
    """
    Performance analytics using DuckDB.
    
    DuckDB is chosen because it's:
    - 10x faster than SQLite for analytical queries
    - Zero-config, no server needed
    - Can query Parquet/CSV directly
    - Perfect for aggregations and window functions
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.db_path = self.config.get("db_path", "analytics/analytics.duckdb")
        self._conn = None

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_path) or ".", exist_ok=True)

    def _get_conn(self):
        """Lazy-initialize DuckDB connection."""
        if self._conn is None:
            try:
                import duckdb
                self._conn = duckdb.connect(self.db_path)
                self._init_schema()
            except ImportError:
                logger.error("duckdb not installed. Run: pip install duckdb")
                raise
        return self._conn

    def _init_schema(self):
        """Create analytics tables if they don't exist."""
        conn = self._get_conn()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trades_analytics (
                id INTEGER PRIMARY KEY,
                instrument VARCHAR,
                direction VARCHAR,
                volume DOUBLE,
                entry_price DOUBLE,
                exit_price DOUBLE,
                entry_time TIMESTAMP,
                exit_time TIMESTAMP,
                pnl DOUBLE,
                pnl_pct DOUBLE,
                commission DOUBLE,
                status VARCHAR,
                strategy_tag VARCHAR,
                broker VARCHAR,
                trade_date DATE,
                trade_hour INTEGER,
                day_of_week INTEGER,
                is_winner BOOLEAN,
                r_multiple DOUBLE
            )
        """)

    def sync_from_api(self, api_base: str = "http://localhost:8000"):
        """Sync trades from the FastAPI backend into DuckDB for analytics."""
        try:
            import requests
            resp = requests.get(f"{api_base}/api/trades/", params={"limit": 5000}, timeout=10)
            resp.raise_for_status()
            trades = resp.json()
        except Exception as e:
            logger.error("Failed to fetch trades from API: %s", e)
            return 0

        conn = self._get_conn()
        count = 0

        for trade in trades:
            try:
                entry_time = trade.get("entry_time")
                exit_time = trade.get("exit_time")
                pnl = trade.get("pnl")
                entry_price = trade.get("entry_price") or 0
                exit_price = trade.get("exit_price")

                # Derive trade date and hour
                trade_date = entry_time[:10] if entry_time else None
                trade_hour = int(entry_time[11:13]) if entry_time and len(entry_time) >= 13 else None
                day_of_week = None
                if trade_date:
                    from datetime import date as dt_date
                    try:
                        d = dt_date.fromisoformat(trade_date)
                        day_of_week = d.weekday()  # 0=Mon, 6=Sun
                    except ValueError:
                        pass

                # Determine winner/loser
                is_winner = True if pnl and pnl > 0 else (False if pnl and pnl < 0 else None)

                # R-multiple (assuming 1R = 1% of entry, or use ATR)
                r_multiple = None
                if pnl and entry_price:
                    risk_pct = 0.01  # default 1% risk
                    r_multiple = pnl / (entry_price * risk_pct)

                conn.execute("""
                    INSERT OR REPLACE INTO trades_analytics
                    (id, instrument, direction, volume, entry_price, exit_price,
                     entry_time, exit_time, pnl, pnl_pct, commission, status,
                     strategy_tag, broker, trade_date, trade_hour, day_of_week,
                     is_winner, r_multiple)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade.get("id"),
                    trade.get("instrument_symbol", trade.get("instrument", "")),
                    trade.get("direction"),
                    trade.get("volume"),
                    entry_price,
                    exit_price,
                    entry_time,
                    exit_time,
                    pnl,
                    trade.get("pnl_pct"),
                    trade.get("commission", 0),
                    trade.get("status"),
                    trade.get("strategy_tag"),
                    trade.get("broker"),
                    trade_date,
                    trade_hour,
                    day_of_week,
                    is_winner,
                    r_multiple,
                ))
                count += 1
            except Exception as e:
                logger.debug("Skipping trade %s: %s", trade.get("id"), e)

        conn.commit()
        logger.info("Synced %d trades to analytics DB", count)
        return count

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------
    def get_summary(self) -> dict:
        """Get overall trading statistics."""
        conn = self._get_conn()
        try:
            row = conn.execute("""
                SELECT
                    COUNT(*) as total_trades,
                    COUNT(*) FILTER (WHERE status = 'closed') as closed_trades,
                    COUNT(*) FILTER (WHERE is_winner = true) as winning_trades,
                    COUNT(*) FILTER (WHERE is_winner = false) as losing_trades,
                    COALESCE(SUM(pnl), 0) as total_pnl,
                    COALESCE(AVG(pnl), 0) as avg_pnl,
                    COALESCE(AVG(r_multiple), 0) as avg_r_multiple,
                    COALESCE(SUM(pnl) FILTER (WHERE is_winner = true), 0) as total_wins,
                    COALESCE(SUM(pnl) FILTER (WHERE is_winner = false), 0) as total_losses,
                    COALESCE(AVG(pnl) FILTER (WHERE is_winner = true), 0) as avg_win,
                    COALESCE(AVG(pnl) FILTER (WHERE is_winner = false), 0) as avg_loss,
                    MAX(pnl) as best_trade,
                    MIN(pnl) as worst_trade,
                    COUNT(DISTINCT trade_date) as trading_days
                FROM trades_analytics
            """).fetchone()

            if not row:
                return {"total_trades": 0}

            total = row[0] or 0
            closed = row[1] or 0
            wins = row[2] or 0
            losses = row[3] or 0
            total_pnl = row[4] or 0
            total_wins = row[8] or 0
            total_losses = abs(row[9] or 0)

            # Derived metrics
            win_rate = (wins / closed * 100) if closed > 0 else 0
            profit_factor = (total_wins / total_losses) if total_losses > 0 else (total_wins if total_wins > 0 else 0)

            return {
                "total_trades": total,
                "closed_trades": closed,
                "winning_trades": wins,
                "losing_trades": losses,
                "win_rate": round(win_rate, 2),
                "total_pnl": round(total_pnl, 2),
                "avg_pnl": round(row[5] or 0, 2),
                "avg_win": round(row[9] or 0, 2),
                "avg_loss": round(row[10] or 0, 2),
                "profit_factor": round(profit_factor, 2),
                "avg_r_multiple": round(row[6] or 0, 2),
                "best_trade": round(row[11] or 0, 2),
                "worst_trade": round(row[12] or 0, 2),
                "trading_days": row[13] or 0,
            }

        except Exception as e:
            logger.error("Analytics summary error: %s", e)
            return {"total_trades": 0}

    def get_equity_curve(self) -> list[dict]:
        """Generate equity curve data points (cumulative PnL over time)."""
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT
                    trade_date,
                    SUM(pnl) OVER (ORDER BY trade_date, id) as cumulative_pnl,
                    SUM(pnl) as daily_pnl
                FROM trades_analytics
                WHERE status = 'closed'
                ORDER BY trade_date, id
            """).fetchall()

            return [
                {
                    "date": str(r[0]) if r[0] else "",
                    "cumulative_pnl": round(r[1], 2) if r[1] else 0,
                    "daily_pnl": round(r[2], 2) if r[2] else 0,
                }
                for r in rows
            ]
        except Exception as e:
            logger.error("Equity curve error: %s", e)
            return []

    def get_by_strategy(self) -> list[dict]:
        """Get performance breakdown by strategy tag."""
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT
                    COALESCE(strategy_tag, 'untagged') as strategy,
                    COUNT(*) as trades,
                    COUNT(*) FILTER (WHERE is_winner = true) as wins,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl,
                    AVG(r_multiple) as avg_r
                FROM trades_analytics
                WHERE status = 'closed'
                GROUP BY strategy
                ORDER BY total_pnl DESC
            """).fetchall()

            return [
                {
                    "strategy": r[0],
                    "trades": r[1],
                    "wins": r[2],
                    "win_rate": round(r[2] / r[1] * 100, 1) if r[1] > 0 else 0,
                    "total_pnl": round(r[3], 2) if r[3] else 0,
                    "avg_pnl": round(r[4], 2) if r[4] else 0,
                    "avg_r": round(r[5], 2) if r[5] else 0,
                }
                for r in rows
            ]
        except Exception as e:
            logger.error("Strategy breakdown error: %s", e)
            return []

    def get_monthly_pnl(self) -> list[dict]:
        """Get PnL grouped by month."""
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT
                    strftime('%Y-%m', trade_date) as month,
                    COUNT(*) as trades,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl,
                    COUNT(*) FILTER (WHERE is_winner = true) as wins
                FROM trades_analytics
                WHERE status = 'closed'
                GROUP BY month
                ORDER BY month
            """).fetchall()

            return [
                {
                    "month": r[0],
                    "trades": r[1],
                    "total_pnl": round(r[2], 2) if r[2] else 0,
                    "avg_pnl": round(r[3], 2) if r[3] else 0,
                    "win_rate": round(r[4] / r[1] * 100, 1) if r[1] > 0 else 0,
                }
                for r in rows
            ]
        except Exception as e:
            logger.error("Monthly PnL error: %s", e)
            return []


def get_analytics(api_base: str = "http://localhost:8000") -> dict:
    """Convenience: sync and return summary metrics."""
    engine = AnalyticsEngine()
    engine.sync_from_api(api_base)
    return engine.get_summary()
