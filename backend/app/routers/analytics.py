"""
DuckDB-powered analytics endpoints for advanced trading metrics.
Provides Sharpe, Sortino, equity curve, MFE/MAE, and rolling windows.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.analytics import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

analytics = AnalyticsService()


@router.post("/sync")
def sync_analytics(db: Session = Depends(get_db)):
    """Sync closed trades from SQLite to DuckDB for analytics queries."""
    try:
        count = analytics.sync_from_db(db)
        return {"synced": count, "status": "ok"}
    except Exception as e:
        logger.exception("Analytics sync failed")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/summary")
def get_analytics_summary():
    """Get comprehensive trading statistics from DuckDB."""
    try:
        return analytics.get_summary()
    except ImportError:
        raise HTTPException(status_code=503, detail="DuckDB not installed. Run: pip install duckdb")
    except Exception as e:
        logger.exception("Analytics summary failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/equity-curve")
def get_equity_curve():
    """Get equity curve data points (cumulative PnL over time)."""
    try:
        return analytics.get_equity_curve()
    except Exception as e:
        logger.exception("Equity curve failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mfe-mae")
def get_mfe_mae():
    """
    Get MFE/MAE (Maximum Favorable/Adverse Excursion) for each trade.
    
    Estimates from entry/exit prices. For precise MFE/MAE, intraday
    bar data would be needed.
    """
    try:
        return analytics.get_mfe_mae()
    except Exception as e:
        logger.exception("MFE/MAE failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rolling")
def get_rolling_metrics(
    window: int = Query(20, ge=5, le=200, description="Rolling window size in trades"),
):
    """Get rolling window performance metrics."""
    try:
        return analytics.get_rolling_metrics(window=window)
    except Exception as e:
        logger.exception("Rolling metrics failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-strategy")
def get_by_strategy():
    """Get performance breakdown by strategy."""
    try:
        return analytics.get_by_strategy()
    except Exception as e:
        logger.exception("Strategy breakdown failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-month")
def get_by_month():
    """Get monthly PnL breakdown."""
    try:
        return analytics.get_monthly_pnl()
    except Exception as e:
        logger.exception("Monthly PnL failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-setup")
def get_by_setup():
    """Get performance breakdown by setup type."""
    try:
        return analytics.get_by_setup_type()
    except Exception as e:
        logger.exception("Setup breakdown failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/by-day-of-week")
def get_by_day_of_week():
    """Get performance breakdown by day of week."""
    try:
        return analytics.get_by_day_of_week()
    except Exception as e:
        logger.exception("Day of week breakdown failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sharpe")
def get_sharpe_ratio():
    """Get annualized Sharpe ratio."""
    try:
        summary = analytics.get_summary()
        return {"sharpe_ratio": summary.get("sharpe_ratio", 0.0)}
    except Exception as e:
        logger.exception("Sharpe ratio failed")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sortino")
def get_sortino_ratio():
    """Get annualized Sortino ratio."""
    try:
        summary = analytics.get_summary()
        return {"sortino_ratio": summary.get("sortino_ratio", 0.0)}
    except Exception as e:
        logger.exception("Sortino ratio failed")
        raise HTTPException(status_code=500, detail=str(e))
