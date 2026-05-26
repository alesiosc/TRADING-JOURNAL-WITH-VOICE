"""
Stats calculation engine for the Trading Journal.
Computes all performance metrics from closed trades using SQLite.
"""
import math
from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
from collections import defaultdict

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Trade, Instrument


def compute_stats(
    db: Session,
    instrument_id: int = None,
    start_date: str = None,
    end_date: str = None,
    strategy: str = None,
    setup_type: str = None,
    broker: str = None,
) -> dict:
    """
    Compute comprehensive trading statistics.

    All filter parameters are optional. When omitted, uses all closed trades.
    """
    # Build base query for closed trades
    query = db.query(Trade).filter(Trade.status == "closed")

    if instrument_id is not None:
        query = query.filter(Trade.instrument_id == instrument_id)
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(Trade.exit_time >= start_dt)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(Trade.exit_time <= end_dt)
        except ValueError:
            pass
    if strategy:
        query = query.filter(
            (Trade.strategy == strategy) | (Trade.strategy_tag == strategy)
        )
    if setup_type:
        query = query.filter(Trade.setup_type == setup_type)
    if broker:
        query = query.filter(Trade.broker == broker)

    trades: List[Trade] = query.order_by(Trade.exit_time.asc()).all()

    total = len(trades)
    if total == 0:
        return _empty_stats()

    # Classify trades
    winning = [t for t in trades if t.pnl is not None and t.pnl > 0]
    losing = [t for t in trades if t.pnl is not None and t.pnl < 0]
    breakeven = [t for t in trades if t.pnl is not None and t.pnl == 0]

    win_count = len(winning)
    loss_count = len(losing)
    be_count = len(breakeven)

    # Basic aggregates
    gross_profit = sum(t.pnl for t in winning) if winning else 0.0
    gross_loss = abs(sum(t.pnl for t in losing)) if losing else 0.0
    total_pnl = sum(t.pnl or 0.0 for t in trades)
    total_fees = sum(t.fees or t.commission or 0.0 for t in trades)
    total_commissions = sum(t.commission or 0.0 for t in trades)
    net_pnl = total_pnl - total_fees

    # Win Rate
    closed_total = win_count + loss_count
    win_rate = (win_count / closed_total * 100) if closed_total > 0 else 0.0

    # Profit Factor
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (float("inf") if gross_profit > 0 else 0.0)

    # Average Win / Average Loss
    avg_win = (sum(t.pnl for t in winning) / win_count) if win_count > 0 else 0.0
    avg_loss = (sum(t.pnl for t in losing) / loss_count) if loss_count > 0 else 0.0

    # Win/Loss Ratio
    win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0

    # Expectancy
    expectancy = (win_rate / 100.0 * avg_win) + ((1.0 - win_rate / 100.0) * avg_loss)

    # Average R-Value — PnL normalised by (entry_price * tick_size * point_value)
    r_values = []
    for t in trades:
        instr = t.instrument if t.instrument else db.query(Instrument).filter(Instrument.id == t.instrument_id).first()
        if instr and instr.tick_size and instr.point_value and t.entry_price:
            denominator = t.entry_price * instr.tick_size * instr.point_value
            if denominator != 0:
                r_val = (t.pnl or 0.0) / denominator
                r_values.append(r_val)
    avg_r_value = sum(r_values) / len(r_values) if r_values else 0.0

    # PnL list (for sharpe, drawdown)
    pnl_values = [t.pnl or 0.0 for t in trades]

    # Sharpe Ratio (simplified annualised)
    if len(pnl_values) > 1:
        mean_pnl = sum(pnl_values) / len(pnl_values)
        variance = sum((x - mean_pnl) ** 2 for x in pnl_values) / (len(pnl_values) - 1)
        std_pnl = math.sqrt(variance) if variance > 0 else 1e-10
        sharpe_ratio = (mean_pnl / std_pnl) * math.sqrt(252)
    else:
        sharpe_ratio = 0.0

    # Sortino Ratio (downside deviation only)
    if len(pnl_values) > 1:
        mean_pnl = sum(pnl_values) / len(pnl_values)
        downside_sq = sum((x - mean_pnl) ** 2 for x in pnl_values if x < mean_pnl)
        downside_var = downside_sq / (len(pnl_values) - 1)
        downside_std = math.sqrt(downside_var) if downside_var > 0 else 1e-10
        sortino_ratio = (mean_pnl / downside_std) * math.sqrt(252)
    else:
        sortino_ratio = 0.0

    # Max Drawdown from equity curve
    cumulative = 0.0
    peak = float("-inf")
    max_drawdown = 0.0
    for t in trades:
        cumulative += t.pnl or 0.0
        if cumulative > peak:
            peak = cumulative
        drawdown = peak - cumulative
        if drawdown > max_drawdown:
            max_drawdown = drawdown

    equity_curve_data = []
    running = 0.0
    for t in trades:
        running += t.pnl or 0.0
        exit_dt = t.exit_time or t.updated_at or datetime.utcnow()
        equity_curve_data.append({
            "date": exit_dt.isoformat(),
            "cumulative_pnl": round(running, 4),
        })

    # Max Consecutive Wins / Losses
    max_win_streak = 0
    max_loss_streak = 0
    current_win_streak = 0
    current_loss_streak = 0
    for t in trades:
        if t.pnl is not None and t.pnl > 0:
            current_win_streak += 1
            current_loss_streak = 0
            max_win_streak = max(max_win_streak, current_win_streak)
        elif t.pnl is not None and t.pnl < 0:
            current_loss_streak += 1
            current_win_streak = 0
            max_loss_streak = max(max_loss_streak, current_loss_streak)
        else:
            current_win_streak = 0
            current_loss_streak = 0

    # Best / Worst Trade
    best_trade = None
    worst_trade = None
    if winning:
        best = max(winning, key=lambda t: t.pnl)
        best_trade = {
            "id": best.id,
            "pnl": best.pnl,
            "symbol": best.instrument.symbol if best.instrument else (best.symbol or str(best.instrument_id)),
            "date": best.exit_time.isoformat() if best.exit_time else None,
        }
    if losing:
        worst = min(losing, key=lambda t: t.pnl)
        worst_trade = {
            "id": worst.id,
            "pnl": worst.pnl,
            "symbol": worst.instrument.symbol if worst.instrument else (best.symbol if 'best' in dir() else str(worst.instrument_id)),
            "date": worst.exit_time.isoformat() if worst.exit_time else None,
        }

    # Average Hold Time
    hold_times = []
    for t in trades:
        if t.entry_time and t.exit_time:
            duration = t.exit_time - t.entry_time
            hold_times.append(duration.total_seconds())
    avg_hold_seconds = sum(hold_times) / len(hold_times) if hold_times else 0.0
    avg_hold_minutes = avg_hold_seconds / 60.0

    # PnL by Instrument
    by_instrument = defaultdict(lambda: {"total_pnl": 0.0, "trade_count": 0})
    for t in trades:
        sym = t.instrument.symbol if t.instrument else (t.symbol or str(t.instrument_id))
        by_instrument[sym]["total_pnl"] += t.pnl or 0.0
        by_instrument[sym]["trade_count"] += 1
    pnl_by_instrument = {k: dict(v) for k, v in sorted(by_instrument.items(), key=lambda x: x[1]["total_pnl"], reverse=True)}

    # PnL by Month
    by_month = defaultdict(lambda: {"total_pnl": 0.0, "trade_count": 0, "win_count": 0})
    for t in trades:
        if t.exit_time:
            key = t.exit_time.strftime("%Y-%m")
            by_month[key]["total_pnl"] += t.pnl or 0.0
            by_month[key]["trade_count"] += 1
            if t.pnl is not None and t.pnl > 0:
                by_month[key]["win_count"] += 1
    pnl_by_month = {k: dict(v) for k, v in sorted(by_month.items())}

    # PnL by Strategy
    by_strategy = defaultdict(lambda: {"total_pnl": 0.0, "trade_count": 0, "win_count": 0})
    for t in trades:
        strat = t.strategy or t.strategy_tag or "untagged"
        by_strategy[strat]["total_pnl"] += t.pnl or 0.0
        by_strategy[strat]["trade_count"] += 1
        if t.pnl is not None and t.pnl > 0:
            by_strategy[strat]["win_count"] += 1
    pnl_by_strategy = {k: dict(v) for k, v in sorted(by_strategy.items(), key=lambda x: x[1]["total_pnl"], reverse=True)}

    # PnL by Setup Type
    by_setup = defaultdict(lambda: {"total_pnl": 0.0, "trade_count": 0, "win_count": 0})
    for t in trades:
        setup = t.setup_type or "unknown"
        by_setup[setup]["total_pnl"] += t.pnl or 0.0
        by_setup[setup]["trade_count"] += 1
        if t.pnl is not None and t.pnl > 0:
            by_setup[setup]["win_count"] += 1
    pnl_by_setup = {k: dict(v) for k, v in sorted(by_setup.items(), key=lambda x: x[1]["total_pnl"], reverse=True)}

    stats = {
        "total_pnl": round(total_pnl, 4),
        "net_pnl": round(net_pnl, 4),
        "total_fees": round(total_fees, 4),
        "total_commissions": round(total_commissions, 4),
        "gross_profit": round(gross_profit, 4),
        "gross_loss": round(gross_loss, 4),
        "trade_count": {
            "total": total,
            "winning": win_count,
            "losing": loss_count,
            "breakeven": be_count,
        },
        "win_rate": round(win_rate, 2),
        "profit_factor": round(profit_factor, 4) if profit_factor != float("inf") else float("inf"),
        "avg_win": round(avg_win, 4),
        "avg_loss": round(avg_loss, 4),
        "win_loss_ratio": round(win_loss_ratio, 4),
        "expectancy": round(expectancy, 4),
        "avg_r_value": round(avg_r_value, 4),
        "sharpe_ratio": round(sharpe_ratio, 4),
        "sortino_ratio": round(sortino_ratio, 4),
        "max_drawdown": round(max_drawdown, 4),
        "max_consecutive_wins": max_win_streak,
        "max_consecutive_losses": max_loss_streak,
        "avg_hold_time_minutes": round(avg_hold_minutes, 2),
        "best_trade": best_trade,
        "worst_trade": worst_trade,
        "equity_curve": equity_curve_data,
        "pnl_by_instrument": pnl_by_instrument,
        "pnl_by_month": pnl_by_month,
        "pnl_by_strategy": pnl_by_strategy,
        "pnl_by_setup": pnl_by_setup,
    }

    return stats


def compute_equity_curve(
    db: Session,
    instrument_id: int = None,
    start_date: str = None,
    end_date: str = None,
) -> list:
    """Return just the equity curve data points."""
    stats = compute_stats(db, instrument_id, start_date, end_date)
    return stats.get("equity_curve", [])


def compute_by_instrument(
    db: Session,
    start_date: str = None,
    end_date: str = None,
) -> dict:
    """Return PnL grouped by instrument."""
    stats = compute_stats(db, None, start_date, end_date)
    return stats.get("pnl_by_instrument", {})


def compute_by_month(
    db: Session,
    instrument_id: int = None,
    start_date: str = None,
    end_date: str = None,
) -> dict:
    """Return PnL grouped by month."""
    stats = compute_stats(db, instrument_id, start_date, end_date)
    return stats.get("pnl_by_month", {})


def compute_by_strategy(
    db: Session,
    start_date: str = None,
    end_date: str = None,
) -> dict:
    """Return PnL grouped by strategy."""
    stats = compute_stats(db, None, start_date, end_date)
    return stats.get("pnl_by_strategy", {})


def compute_by_setup(
    db: Session,
    start_date: str = None,
    end_date: str = None,
) -> dict:
    """Return PnL grouped by setup type."""
    stats = compute_stats(db, None, start_date, end_date)
    return stats.get("pnl_by_setup", {})


def _empty_stats() -> dict:
    """Return a zeroed-out stats dict when there are no trades."""
    return {
        "total_pnl": 0.0,
        "net_pnl": 0.0,
        "total_fees": 0.0,
        "total_commissions": 0.0,
        "gross_profit": 0.0,
        "gross_loss": 0.0,
        "trade_count": {"total": 0, "winning": 0, "losing": 0, "breakeven": 0},
        "win_rate": 0.0,
        "profit_factor": 0.0,
        "avg_win": 0.0,
        "avg_loss": 0.0,
        "win_loss_ratio": 0.0,
        "expectancy": 0.0,
        "avg_r_value": 0.0,
        "sharpe_ratio": 0.0,
        "sortino_ratio": 0.0,
        "max_drawdown": 0.0,
        "max_consecutive_wins": 0,
        "max_consecutive_losses": 0,
        "avg_hold_time_minutes": 0.0,
        "best_trade": None,
        "worst_trade": None,
        "equity_curve": [],
        "pnl_by_instrument": {},
        "pnl_by_month": {},
        "pnl_by_strategy": {},
        "pnl_by_setup": {},
    }
