"""
DuckDB analytics service for advanced trading performance metrics.

Provides:
  - Sharpe & Sortino ratios
  - Equity curve generation
  - MFE/MAE (Maximum Favorable/Adverse Excursion)
  - Rolling window metrics
  - Sync trades from SQLite to DuckDB
"""
import logging
import math
import os
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from app.config import settings

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Performance analytics using DuckDB for fast analytical queries.
    DuckDB is zero-config, embedded, and optimized for aggregation queries.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.ANALYTICS_DB_PATH
        self._ensure_dir()
        self._conn = None

    def _ensure_dir(self):
        """Ensure the directory for the DuckDB file exists."""
        d = os.path.dirname(self.db_path)
        if d:
            os.makedirs(d, exist_ok=True)

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
                symbol VARCHAR,
                direction VARCHAR,
                volume DOUBLE,
                entry_price DOUBLE,
                exit_price DOUBLE,
                stop_loss DOUBLE,
                take_profit DOUBLE,
                entry_time TIMESTAMP,
                exit_time TIMESTAMP,
                pnl DOUBLE,
                pnl_pct DOUBLE,
                commission DOUBLE,
                fees DOUBLE,
                status VARCHAR,
                strategy VARCHAR,
                strategy_tag VARCHAR,
                setup_type VARCHAR,
                broker VARCHAR,
                account_id VARCHAR,
                rating INTEGER,
                trade_date DATE,
                trade_hour INTEGER,
                day_of_week INTEGER,
                is_winner BOOLEAN,
                r_multiple DOUBLE
            )
        """)

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    def sync_from_db(self, db: Session):
        """
        Sync all closed trades from SQLite to DuckDB for analytics.
        Uses INSERT OR REPLACE for idempotent sync.
        """
        from app.models import Trade, Instrument

        conn = self._get_conn()
        trades = db.query(Trade).filter(Trade.status == "closed").order_by(Trade.exit_time).all()
        count = 0

        for trade in trades:
            try:
                instr = trade.instrument
                symbol = instr.symbol if instr else (trade.symbol or f"ID:{trade.instrument_id}")
                entry_time = trade.entry_time
                exit_time = trade.exit_time
                pnl = trade.pnl
                entry_price = trade.entry_price or 0
                exit_price = trade.exit_price

                # Derive dimensions
                trade_date = entry_time.strftime("%Y-%m-%d") if entry_time else None
                trade_hour = entry_time.hour if entry_time else None
                day_of_week = entry_time.weekday() if entry_time else None  # 0=Mon

                is_winner = True if pnl and pnl > 0 else (False if pnl and pnl < 0 else None)

                # R-multiple: pnl / (entry_price * 0.01) as a simple approximation
                r_multiple = None
                if pnl is not None and entry_price and entry_price > 0:
                    risk_pct = 0.01
                    r_multiple = pnl / (entry_price * risk_pct)

                conn.execute("""
                    INSERT OR REPLACE INTO trades_analytics (
                        id, instrument, symbol, direction, volume,
                        entry_price, exit_price, stop_loss, take_profit,
                        entry_time, exit_time, pnl, pnl_pct, commission, fees,
                        status, strategy, strategy_tag, setup_type,
                        broker, account_id, rating,
                        trade_date, trade_hour, day_of_week,
                        is_winner, r_multiple
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                              ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    trade.id,
                    symbol,
                    symbol,
                    trade.direction,
                    trade.volume,
                    entry_price,
                    exit_price,
                    trade.stop_loss,
                    trade.take_profit,
                    entry_time.isoformat() if entry_time else None,
                    exit_time.isoformat() if exit_time else None,
                    pnl,
                    trade.pnl_pct,
                    trade.commission or 0,
                    trade.fees or 0,
                    trade.status,
                    trade.strategy or trade.strategy_tag,
                    trade.strategy_tag,
                    trade.setup_type,
                    trade.broker,
                    trade.account_id,
                    trade.rating,
                    trade_date,
                    trade_hour,
                    day_of_week,
                    is_winner,
                    r_multiple,
                ))
                count += 1
            except Exception as e:
                logger.debug("Skipping trade %d: %s", trade.id, e)

        conn.commit()
        logger.info("Synced %d trades to DuckDB analytics", count)
        return count

    # ------------------------------------------------------------------
    # Summary metrics
    # ------------------------------------------------------------------

    def get_summary(self) -> dict:
        """Get comprehensive trading statistics from DuckDB."""
        conn = self._get_conn()
        try:
            row = conn.execute("""
                SELECT
                    COUNT(*) as total_trades,
                    COUNT(*) FILTER (WHERE status = 'closed') as closed_trades,
                    COUNT(*) FILTER (WHERE is_winner = true) as winning_trades,
                    COUNT(*) FILTER (WHERE is_winner = false) as losing_trades,
                    COUNT(*) FILTER (WHERE is_winner IS NULL) as breakeven_trades,
                    COALESCE(SUM(pnl), 0) as total_pnl,
                    COALESCE(AVG(pnl), 0) as avg_pnl,
                    COALESCE(SUM(pnl) FILTER (WHERE is_winner = true), 0) as gross_profit,
                    COALESCE(SUM(pnl) FILTER (WHERE is_winner = false), 0) as gross_loss,
                    COALESCE(AVG(pnl) FILTER (WHERE is_winner = true), 0) as avg_win,
                    COALESCE(AVG(pnl) FILTER (WHERE is_winner = false), 0) as avg_loss,
                    COALESCE(AVG(r_multiple), 0) as avg_r_multiple,
                    MAX(pnl) as best_trade,
                    MIN(pnl) as worst_trade,
                    COUNT(DISTINCT trade_date) as trading_days
                FROM trades_analytics
                WHERE status = 'closed'
            """).fetchone()

            if not row or row[0] == 0:
                return self._empty_summary()

            total = row[0] or 0
            closed = row[1] or 0
            wins = row[2] or 0
            losses = row[3] or 0
            total_pnl = row[5] or 0
            gross_profit = abs(row[7] or 0)
            gross_loss = abs(row[8] or 0)

            # Win Rate
            win_rate = (wins / closed * 100) if closed > 0 else 0

            # Profit Factor
            profit_factor = float("inf") if gross_loss == 0 and gross_profit > 0 else 0.0
            if gross_loss > 0:
                profit_factor = gross_profit / gross_loss

            # Expectancy = (Win% * AvgWin) + (Loss% * AvgLoss)
            avg_win = row[9] or 0
            avg_loss = row[10] or 0
            expectancy = (win_rate / 100 * avg_win) + ((1 - win_rate / 100) * avg_loss)

            # Sharpe & Sortino from individual PnLs
            sharpe = self._compute_sharpe_ratio()
            sortino = self._compute_sortino_ratio()

            # Max Drawdown
            max_dd = self._compute_max_drawdown()

            return {
                "total_trades": total,
                "closed_trades": closed,
                "winning_trades": wins,
                "losing_trades": losses,
                "breakeven_trades": row[4] or 0,
                "win_rate": round(win_rate, 2),
                "total_pnl": round(total_pnl, 2),
                "gross_profit": round(gross_profit, 2),
                "gross_loss": round(gross_loss, 2),
                "avg_pnl": round(row[6] or 0, 2),
                "avg_win": round(avg_win, 2),
                "avg_loss": round(avg_loss, 2),
                "profit_factor": round(profit_factor, 4) if profit_factor != float("inf") else "inf",
                "expectancy": round(expectancy, 4),
                "avg_r_multiple": round(row[11] or 0, 4),
                "sharpe_ratio": round(sharpe, 4),
                "sortino_ratio": round(sortino, 4),
                "max_drawdown": round(max_dd, 2),
                "best_trade": round(row[12] or 0, 2),
                "worst_trade": round(row[13] or 0, 2),
                "trading_days": row[14] or 0,
            }
        except Exception as e:
            logger.error("Analytics summary error: %s", e)
            return self._empty_summary()

    def _empty_summary(self) -> dict:
        return {
            "total_trades": 0,
            "closed_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "breakeven_trades": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "avg_pnl": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "profit_factor": 0.0,
            "expectancy": 0.0,
            "avg_r_multiple": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0,
            "max_drawdown": 0.0,
            "best_trade": None,
            "worst_trade": None,
            "trading_days": 0,
        }

    # ------------------------------------------------------------------
    # Sharpe & Sortino
    # ------------------------------------------------------------------

    def _compute_sharpe_ratio(self) -> float:
        """Compute annualized Sharpe ratio from individual trade PnLs."""
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT pnl FROM trades_analytics
                WHERE status = 'closed' AND pnl IS NOT NULL
                ORDER BY exit_time
            """).fetchall()
        except Exception:
            return 0.0

        values = [r[0] for r in rows]
        return self._sharpe_from_values(values)

    def _compute_sortino_ratio(self) -> float:
        """Compute annualized Sortino ratio (uses downside deviation only)."""
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT pnl FROM trades_analytics
                WHERE status = 'closed' AND pnl IS NOT NULL
                ORDER BY exit_time
            """).fetchall()
        except Exception:
            return 0.0

        values = [r[0] for r in rows]
        return self._sortino_from_values(values)

    @staticmethod
    def _sharpe_from_values(values: List[float], annual_factor: float = 252) -> float:
        """Compute annualized Sharpe ratio from a list of trade PnLs."""
        if len(values) < 2:
            return 0.0
        n = len(values)
        mean_val = sum(values) / n
        variance = sum((x - mean_val) ** 2 for x in values) / (n - 1)
        if variance <= 0:
            return 0.0
        std_dev = math.sqrt(variance)
        if std_dev == 0:
            return 0.0
        return (mean_val / std_dev) * math.sqrt(annual_factor)

    @staticmethod
    def _sortino_from_values(values: List[float], annual_factor: float = 252) -> float:
        """Compute annualized Sortino ratio (downside deviation only)."""
        if len(values) < 2:
            return 0.0
        n = len(values)
        mean_val = sum(values) / n

        # Downside deviation: only negative deviations
        downside_sq_sum = sum((x - mean_val) ** 2 for x in values if x < mean_val)
        downside_var = downside_sq_sum / (n - 1) if n > 1 else 0
        if downside_var <= 0:
            return 0.0
        downside_std = math.sqrt(downside_var)
        if downside_std == 0:
            return 0.0
        return (mean_val / downside_std) * math.sqrt(annual_factor)

    # ------------------------------------------------------------------
    # Max Drawdown
    # ------------------------------------------------------------------

    def _compute_max_drawdown(self) -> float:
        """Compute maximum drawdown from equity curve."""
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT pnl FROM trades_analytics
                WHERE status = 'closed' AND pnl IS NOT NULL
                ORDER BY exit_time
            """).fetchall()
        except Exception:
            return 0.0

        cumulative = 0.0
        peak = float("-inf")
        max_dd = 0.0
        for r in rows:
            cumulative += r[0]
            if cumulative > peak:
                peak = cumulative
            dd = peak - cumulative
            if dd > max_dd:
                max_dd = dd
        return max_dd

    # ------------------------------------------------------------------
    # Equity Curve
    # ------------------------------------------------------------------

    def get_equity_curve(self) -> List[dict]:
        """Generate equity curve data points (cumulative PnL over time)."""
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT
                    exit_time,
                    pnl
                FROM trades_analytics
                WHERE status = 'closed' AND pnl IS NOT NULL AND exit_time IS NOT NULL
                ORDER BY exit_time, id
            """).fetchall()
        except Exception as e:
            logger.error("Equity curve error: %s", e)
            return []

        curve = []
        cumulative = 0.0
        for r in rows:
            cumulative += r[1]
            curve.append({
                "date": str(r[0]) if r[0] else "",
                "cumulative_pnl": round(cumulative, 2),
                "trade_pnl": round(r[1], 2),
            })
        return curve

    # ------------------------------------------------------------------
    # MFE / MAE (Maximum Favorable/Adverse Excursion)
    # ------------------------------------------------------------------

    def get_mfe_mae(self) -> List[dict]:
        """
        Estimate MFE/MAE for each trade.
        
        Since we don't have intraday tick data in the trades table,
        we approximate MFE/MAE from available data:
        - MFE ≈ max(0, exit_price - entry_price) * direction multiplier
        - MAE ≈ min(0, exit_price - entry_price) * direction multiplier
        
        For a more accurate calculation, intraday bar data would be needed.
        """
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT
                    id, direction, entry_price, exit_price, pnl
                FROM trades_analytics
                WHERE status = 'closed' AND entry_price IS NOT NULL
                      AND exit_price IS NOT NULL AND pnl IS NOT NULL
                ORDER BY id
            """).fetchall()
        except Exception as e:
            logger.error("MFE/MAE error: %s", e)
            return []

        results = []
        for r in rows:
            trade_id, direction, entry, exit_, pnl = r
            price_diff = exit_ - entry
            if direction == "long":
                mfe = max(0, price_diff) / entry * 100
                mae = min(0, price_diff) / entry * 100
            else:
                mfe = max(0, -price_diff) / entry * 100
                mae = min(0, -price_diff) / entry * 100

            results.append({
                "trade_id": trade_id,
                "mfe": round(abs(mfe), 4),
                "mae": round(abs(mae), 4),
                "pnl": round(pnl, 2),
                "mfe_mae_ratio": round(abs(mfe / mae), 4) if mae != 0 else None,
            })
        return results

    # ------------------------------------------------------------------
    # Rolling Window Metrics
    # ------------------------------------------------------------------

    def get_rolling_metrics(self, window: int = 20) -> List[dict]:
        """
        Compute rolling window metrics over the last N trades.
        Uses SQL window functions in DuckDB for efficiency.
        """
        conn = self._get_conn()
        try:
            rows = conn.execute(f"""
                WITH ordered AS (
                    SELECT
                        id,
                        pnl,
                        is_winner,
                        exit_time,
                        ROW_NUMBER() OVER (ORDER BY exit_time, id) as rn
                    FROM trades_analytics
                    WHERE status = 'closed' AND pnl IS NOT NULL
                )
                SELECT
                    rn as trade_number,
                    id as trade_id,
                    exit_time,
                    AVG(pnl) OVER (ORDER BY rn ROWS BETWEEN {window - 1} PRECEDING AND CURRENT ROW) as rolling_avg_pnl,
                    SUM(CASE WHEN is_winner = true THEN 1 ELSE 0 END) OVER
                        (ORDER BY rn ROWS BETWEEN {window - 1} PRECEDING AND CURRENT ROW)::FLOAT / 
                    NULLIF(COUNT(*) OVER (ORDER BY rn ROWS BETWEEN {window - 1} PRECEDING AND CURRENT ROW), 0) * 100
                    as rolling_win_rate
                FROM ordered
                ORDER BY rn
            """).fetchall()
        except Exception as e:
            logger.error("Rolling metrics error: %s", e)
            return []

        return [
            {
                "trade_number": r[0],
                "trade_id": r[1],
                "date": str(r[2]) if r[2] else "",
                "rolling_avg_pnl": round(r[3], 4) if r[3] else 0,
                "rolling_win_rate": round(r[4], 2) if r[4] else 0,
                "window": window,
            }
            for r in rows
        ]

    # ------------------------------------------------------------------
    # Strategy & Monthly breakdowns
    # ------------------------------------------------------------------

    def get_by_strategy(self) -> List[dict]:
        """Get performance breakdown by strategy."""
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT
                    COALESCE(NULLIF(strategy, ''), NULLIF(strategy_tag, ''), 'untagged') as strategy_name,
                    COUNT(*) as trades,
                    COUNT(*) FILTER (WHERE is_winner = true) as wins,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl,
                    AVG(r_multiple) as avg_r
                FROM trades_analytics
                WHERE status = 'closed'
                GROUP BY strategy_name
                ORDER BY total_pnl DESC
            """).fetchall()

            return [
                {
                    "strategy": r[0],
                    "trades": r[1],
                    "wins": r[2],
                    "win_rate": round(r[2] / r[1] * 100, 1) if r[1] > 0 else 0,
                    "total_pnl": round(r[3] or 0, 2),
                    "avg_pnl": round(r[4] or 0, 2),
                    "avg_r": round(r[5] or 0, 2),
                }
                for r in rows
            ]
        except Exception as e:
            logger.error("Strategy breakdown error: %s", e)
            return []

    def get_monthly_pnl(self) -> List[dict]:
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
                WHERE status = 'closed' AND trade_date IS NOT NULL
                GROUP BY month
                ORDER BY month
            """).fetchall()

            return [
                {
                    "month": r[0],
                    "trades": r[1],
                    "total_pnl": round(r[2] or 0, 2),
                    "avg_pnl": round(r[3] or 0, 2),
                    "win_rate": round(r[4] / r[1] * 100, 1) if r[1] > 0 else 0,
                }
                for r in rows
            ]
        except Exception as e:
            logger.error("Monthly PnL error: %s", e)
            return []

    def get_by_setup_type(self) -> List[dict]:
        """Get performance breakdown by setup type."""
        conn = self._get_conn()
        try:
            rows = conn.execute("""
                SELECT
                    COALESCE(NULLIF(setup_type, ''), 'unknown') as setup,
                    COUNT(*) as trades,
                    COUNT(*) FILTER (WHERE is_winner = true) as wins,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl
                FROM trades_analytics
                WHERE status = 'closed'
                GROUP BY setup
                ORDER BY total_pnl DESC
            """).fetchall()

            return [
                {
                    "setup": r[0],
                    "trades": r[1],
                    "wins": r[2],
                    "win_rate": round(r[2] / r[1] * 100, 1) if r[1] > 0 else 0,
                    "total_pnl": round(r[3] or 0, 2),
                    "avg_pnl": round(r[4] or 0, 2),
                }
                for r in rows
            ]
        except Exception as e:
            logger.error("Setup breakdown error: %s", e)
            return []

    def get_by_day_of_week(self) -> List[dict]:
        """Get performance breakdown by day of week."""
        conn = self._get_conn()
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        try:
            rows = conn.execute("""
                SELECT
                    day_of_week,
                    COUNT(*) as trades,
                    COUNT(*) FILTER (WHERE is_winner = true) as wins,
                    SUM(pnl) as total_pnl,
                    AVG(pnl) as avg_pnl
                FROM trades_analytics
                WHERE status = 'closed' AND day_of_week IS NOT NULL
                GROUP BY day_of_week
                ORDER BY day_of_week
            """).fetchall()

            return [
                {
                    "day": days[r[0]] if 0 <= r[0] < 7 else f"Day {r[0]}",
                    "day_number": r[0],
                    "trades": r[1],
                    "wins": r[2],
                    "win_rate": round(r[2] / r[1] * 100, 1) if r[1] > 0 else 0,
                    "total_pnl": round(r[3] or 0, 2),
                    "avg_pnl": round(r[4] or 0, 2),
                }
                for r in rows
            ]
        except Exception as e:
            logger.error("Day of week breakdown error: %s", e)
            return []

    # ------------------------------------------------------------------
    # Close connection
    # ------------------------------------------------------------------

    def close(self):
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None


# Singleton instance
analytics_service = AnalyticsService()
