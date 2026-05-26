from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.stats import (
    compute_stats,
    compute_equity_curve,
    compute_by_instrument,
    compute_by_month,
    compute_by_strategy,
    compute_by_setup,
)

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/summary")
def get_stats_summary(
    instrument_id: int = Query(None, description="Filter by instrument ID"),
    start_date: str = Query(None, description="Start date (ISO format, e.g. 2025-01-01)"),
    end_date: str = Query(None, description="End date (ISO format, e.g. 2025-12-31)"),
    strategy: str = Query(None, description="Filter by strategy name"),
    setup_type: str = Query(None, description="Filter by setup type"),
    broker: str = Query(None, description="Filter by broker"),
    db: Session = Depends(get_db),
):
    """Return all computed trading statistics from the SQLite database."""
    return compute_stats(
        db,
        instrument_id=instrument_id,
        start_date=start_date,
        end_date=end_date,
        strategy=strategy,
        setup_type=setup_type,
        broker=broker,
    )


@router.get("/equity-curve")
def get_equity_curve(
    instrument_id: int = Query(None, description="Filter by instrument ID"),
    start_date: str = Query(None, description="Start date (ISO format)"),
    end_date: str = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db),
):
    """Return equity curve data points for charting."""
    return compute_equity_curve(db, instrument_id=instrument_id, start_date=start_date, end_date=end_date)


@router.get("/by-instrument")
def get_pnl_by_instrument(
    start_date: str = Query(None, description="Start date (ISO format)"),
    end_date: str = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db),
):
    """Return PnL grouped by instrument."""
    return compute_by_instrument(db, start_date=start_date, end_date=end_date)


@router.get("/by-month")
def get_pnl_by_month(
    instrument_id: int = Query(None, description="Filter by instrument ID"),
    start_date: str = Query(None, description="Start date (ISO format)"),
    end_date: str = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db),
):
    """Return PnL grouped by month."""
    return compute_by_month(db, instrument_id=instrument_id, start_date=start_date, end_date=end_date)


@router.get("/by-strategy")
def get_pnl_by_strategy(
    start_date: str = Query(None, description="Start date (ISO format)"),
    end_date: str = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db),
):
    """Return PnL grouped by strategy."""
    return compute_by_strategy(db, start_date=start_date, end_date=end_date)


@router.get("/by-setup")
def get_pnl_by_setup(
    start_date: str = Query(None, description="Start date (ISO format)"),
    end_date: str = Query(None, description="End date (ISO format)"),
    db: Session = Depends(get_db),
):
    """Return PnL grouped by setup type."""
    return compute_by_setup(db, start_date=start_date, end_date=end_date)
