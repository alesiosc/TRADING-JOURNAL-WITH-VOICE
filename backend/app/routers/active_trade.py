"""
Active Trade API endpoints — manage the "currently active" trade context.

Registered under /api/trades/active to keep URLs clean.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models import Trade, Instrument
from app.schemas import TradeRead
from app.services.active_trade import (
    get_active_trade_tracker,
    set_active,
    get_active,
    clear_active,
    get_status,
)


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class ActiveTradeResponse(BaseModel):
    active_trade_id: Optional[int] = None
    active_instrument: Optional[str] = None
    active_window: Optional[str] = None
    trade: Optional[TradeRead] = None


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api/trades/active", tags=["active-trade"])


@router.get("/", response_model=ActiveTradeResponse)
def get_active_trade(db: Session = Depends(get_db)):
    """Get the currently active trade."""
    tracker = get_active_trade_tracker()
    status = tracker.get_status()
    trade_id = status.get("active_trade_id")

    trade = None
    if trade_id is not None:
        trade = db.query(Trade).filter(Trade.id == trade_id).first()

    return ActiveTradeResponse(
        active_trade_id=trade_id,
        active_instrument=status.get("active_instrument"),
        active_window=status.get("active_window"),
        trade=trade,
    )


@router.put("/{trade_id}", response_model=ActiveTradeResponse)
def set_active_trade(trade_id: int, db: Session = Depends(get_db)):
    """Set a trade as the current active trade."""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    instrument = None
    if trade.instrument:
        instrument = trade.instrument.symbol

    set_active(trade_id, instrument=instrument)
    return ActiveTradeResponse(
        active_trade_id=trade_id,
        active_instrument=instrument,
        active_window=None,
        trade=trade,
    )


@router.delete("/", status_code=204)
def delete_active_trade():
    """Clear the active trade."""
    clear_active()
    return None
