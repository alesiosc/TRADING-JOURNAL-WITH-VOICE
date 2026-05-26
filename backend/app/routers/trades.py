from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Trade, TradeLeg, Instrument
from app.schemas import (
    TradeCreate,
    TradeRead,
    TradeUpdate,
    TradeLegCreate,
    TradeLegRead,
)
from app.services.websocket_manager import manager

router = APIRouter(prefix="/api/trades", tags=["trades"])


def _compute_pnl(trade: Trade, instr: Instrument) -> tuple:
    """
    Automatically compute pnl and pnl_pct based on direction, prices, and volume.

    Returns (pnl, pnl_pct).
    """
    if trade.exit_price is None:
        return None, None

    if trade.direction == "long":
        pnl = (trade.exit_price - trade.entry_price) * trade.volume * (instr.point_value or 1.0)
        pnl_pct = ((trade.exit_price - trade.entry_price) / trade.entry_price) * 100
    else:  # short
        pnl = (trade.entry_price - trade.exit_price) * trade.volume * (instr.point_value or 1.0)
        pnl_pct = ((trade.entry_price - trade.exit_price) / trade.entry_price) * 100

    return round(pnl, 4), round(pnl_pct, 4)


def _trade_to_broadcast_dict(trade: Trade) -> dict:
    """Convert a Trade ORM object to a plain dict for WebSocket broadcasting."""
    return {
        "id": trade.id,
        "instrument_id": trade.instrument_id,
        "instrument_symbol": trade.instrument.symbol if trade.instrument else None,
        "direction": trade.direction,
        "volume": trade.volume,
        "entry_price": trade.entry_price,
        "exit_price": trade.exit_price,
        "entry_time": trade.entry_time.isoformat() if trade.entry_time else None,
        "exit_time": trade.exit_time.isoformat() if trade.exit_time else None,
        "pnl": trade.pnl,
        "pnl_pct": trade.pnl_pct,
        "commission": trade.commission,
        "status": trade.status,
        "strategy_tag": trade.strategy_tag,
        "broker": trade.broker,
        "notes": trade.notes,
        "rating": trade.rating,
        "created_at": trade.created_at.isoformat() if trade.created_at else None,
        "updated_at": trade.updated_at.isoformat() if trade.updated_at else None,
    }


@router.get("/", response_model=List[TradeRead])
def list_trades(
    status: str = Query(None, description="Filter by status: open / closed"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Trade)
    if status:
        query = query.filter(Trade.status == status)
    return query.order_by(Trade.entry_time.desc()).offset(skip).limit(limit).all()


@router.get("/{trade_id}", response_model=TradeRead)
def get_trade(trade_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade


@router.post("/", response_model=TradeRead, status_code=201)
async def create_trade(payload: TradeCreate, db: Session = Depends(get_db)):
    # verify instrument exists
    instr = db.query(Instrument).filter(Instrument.id == payload.instrument_id).first()
    if not instr:
        raise HTTPException(status_code=404, detail="Instrument not found")

    trade_data = payload.model_dump(exclude={"legs"}, exclude_unset=False)
    trade = Trade(**trade_data)
    db.add(trade)
    db.flush()  # get trade.id

    # Auto-compute PnL when exit_price is set and status is closed
    if trade.exit_price is not None and trade.status == "closed":
        pnl, pnl_pct = _compute_pnl(trade, instr)
        trade.pnl = pnl
        trade.pnl_pct = pnl_pct
    elif trade.exit_price is not None:
        # If exit_price set but status not 'closed', auto-set to closed
        trade.status = "closed"
        pnl, pnl_pct = _compute_pnl(trade, instr)
        trade.pnl = pnl
        trade.pnl_pct = pnl_pct
        if trade.exit_time is None:
            from datetime import datetime, timezone
            trade.exit_time = datetime.now(timezone.utc)

    # create legs if provided
    if payload.legs:
        for leg_data in payload.legs:
            leg = TradeLeg(trade_id=trade.id, **leg_data.model_dump())
            db.add(leg)

    db.commit()
    db.refresh(trade)
    await manager.broadcast({"type": "trade_created", "data": _trade_to_broadcast_dict(trade)})
    return trade


@router.put("/{trade_id}", response_model=TradeRead)
async def update_trade(trade_id: int, payload: TradeUpdate, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")

    update_data = payload.model_dump(exclude_unset=True)

    # Detect P&L-related transitions before applying updates
    old_status = trade.status
    old_exit_price = trade.exit_price
    old_exit_time = trade.exit_time
    new_status = update_data.get("status", old_status)
    new_exit_price = update_data.get("exit_price", old_exit_price)

    # Apply updates
    for field, value in update_data.items():
        setattr(trade, field, value)

    instr = db.query(Instrument).filter(Instrument.id == trade.instrument_id).first()
    if not instr:
        instr = trade.instrument

    # Detect if this is a close event
    was_closed = (new_exit_price is not None and new_status == "closed") or \
                 (new_exit_price is not None and old_status != "closed")

    # Case 1: Closing the trade - exit_price set and status closed
    if new_exit_price is not None and new_status == "closed":
        pnl, pnl_pct = _compute_pnl(trade, instr)
        trade.pnl = pnl
        trade.pnl_pct = pnl_pct
        if trade.exit_time is None:
            from datetime import datetime, timezone
            trade.exit_time = datetime.now(timezone.utc)
        trade.status = "closed"

    # Case 2: exit_price was set, now being nullified (re-opening)
    elif new_exit_price is None and old_exit_price is not None:
        trade.pnl = None
        trade.pnl_pct = None
        trade.exit_time = None
        trade.status = "open"

    # Case 3: exit_price set but status wasn't changed to closed - auto-close
    elif new_exit_price is not None and new_status != "closed":
        trade.status = "closed"
        pnl, pnl_pct = _compute_pnl(trade, instr)
        trade.pnl = pnl
        trade.pnl_pct = pnl_pct
        if trade.exit_time is None:
            from datetime import datetime, timezone
            trade.exit_time = datetime.now(timezone.utc)

    # Case 4: status changed to closed but no exit_price
    elif new_status == "closed" and new_exit_price is None:
        # This is unusual — leave as-is but mark closed
        trade.status = "closed"

    db.commit()
    db.refresh(trade)

    # Broadcast appropriate event
    if trade.status == "closed" and not was_closed and old_status != "closed":
        await manager.broadcast({"type": "trade_closed", "data": _trade_to_broadcast_dict(trade)})
    else:
        await manager.broadcast({"type": "trade_updated", "data": _trade_to_broadcast_dict(trade)})

    return trade


@router.delete("/{trade_id}", status_code=204)
async def delete_trade(trade_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    db.delete(trade)
    db.commit()
    await manager.broadcast({"type": "trade_deleted", "data": {"id": trade_id}})
    return None


# ---- TradeLeg sub-resource ------------------------------------------------
@router.get("/{trade_id}/legs", response_model=List[TradeLegRead])
def list_trade_legs(trade_id: int, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    return trade.legs


@router.post("/{trade_id}/legs", response_model=TradeLegRead, status_code=201)
def create_trade_leg(trade_id: int, payload: TradeLegCreate, db: Session = Depends(get_db)):
    trade = db.query(Trade).filter(Trade.id == trade_id).first()
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    leg = TradeLeg(trade_id=trade_id, **payload.model_dump())
    db.add(leg)
    db.commit()
    db.refresh(leg)
    return leg
