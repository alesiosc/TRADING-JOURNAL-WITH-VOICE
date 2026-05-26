"""
Voice Trade API endpoints.

- POST /api/voice/parse    — parse natural language into structured trade data
- POST /api/voice/trade    — parse + execute (create/close/modify trade)
- GET  /api/trades/active  — get the currently active trade
- PUT  /api/trades/active/{trade_id} — set a trade as active
- DELETE /api/trades/active — clear active trade
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Trade, TradeLeg, Instrument
from app.schemas import TradeRead
from app.services.voice_trade_parser import parse_voice_text
from app.services.active_trade import (
    get_active_trade_tracker,
    set_active,
    get_active,
    clear_active,
    get_active_instrument,
    set_active_instrument,
)
from app.services.websocket_manager import manager
from app.routers.trades import _trade_to_broadcast_dict

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/voice", tags=["voice"])

# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------


class VoiceParseRequest(BaseModel):
    text: str


class VoiceLeg(BaseModel):
    type: str  # stop / target
    price: float


class VoiceParseResponse(BaseModel):
    success: bool
    intent: str
    instrument: Optional[str] = None
    direction: Optional[str] = None
    volume: Optional[float] = None
    entry_price: Optional[float] = None
    close_price: Optional[float] = None
    stop_price: Optional[float] = None
    target_price: Optional[float] = None
    legs: List[VoiceLeg] = []
    raw_text: str
    notes: Optional[str] = None
    trade: Optional[TradeRead] = None  # populated on execute


class ActiveTradeResponse(BaseModel):
    active_trade_id: Optional[int] = None
    active_instrument: Optional[str] = None
    active_window: Optional[str] = None
    trade: Optional[TradeRead] = None


# ---------------------------------------------------------------------------
# Helper: resolve instrument symbol -> (Instrument, created_flag)
# ---------------------------------------------------------------------------


def _resolve_instrument(db: Session, symbol: str) -> tuple[Instrument, bool]:
    """Find or create an instrument by symbol. Returns (instrument, created)."""
    instr = db.query(Instrument).filter(Instrument.symbol.ilike(symbol)).first()
    if instr:
        return instr, False
    instr = Instrument(symbol=symbol.upper(), name=symbol.upper(), asset_class="futures")
    db.add(instr)
    db.flush()
    return instr, True


# ---------------------------------------------------------------------------
# Helper: find open trade for an instrument
# ---------------------------------------------------------------------------


def _find_open_trade(db: Session, instrument: str) -> Optional[Trade]:
    """Find the most recent open trade for a given instrument symbol."""
    return (
        db.query(Trade)
        .join(Instrument)
        .filter(
            Instrument.symbol.ilike(instrument),
            Trade.status == "open",
        )
        .order_by(Trade.entry_time.desc())
        .first()
    )


# ---------------------------------------------------------------------------
# Helper: broadcast helper
# ---------------------------------------------------------------------------


async def _broadcast_event(event_type: str, trade: Trade):
    """Broadcast a trade event via WebSocket."""
    try:
        await manager.broadcast({"type": event_type, "data": _trade_to_broadcast_dict(trade)})
    except Exception:
        logger.exception("Failed to broadcast %s event", event_type)


# ===========================================================================
# ENDPOINTS
# ===========================================================================


@router.post("/parse", response_model=VoiceParseResponse)
def parse_voice(payload: VoiceParseRequest):
    """
    Parse natural language voice input into structured trade data.
    Does NOT execute any trade action — just parses.
    """
    result = parse_voice_text(payload.text)
    # Build response from parsed result
    resp = VoiceParseResponse(
        success=result.get("success", False),
        intent=result.get("intent", "unknown"),
        instrument=result.get("instrument"),
        direction=result.get("direction"),
        volume=result.get("volume"),
        entry_price=result.get("entry_price"),
        close_price=result.get("close_price"),
        stop_price=result.get("stop_price"),
        target_price=result.get("target_price"),
        legs=[VoiceLeg(**leg) for leg in result.get("legs", [])],
        raw_text=result.get("raw_text", payload.text),
        notes=result.get("notes"),
    )
    return resp


@router.post("/trade", response_model=VoiceParseResponse)
async def voice_trade(payload: VoiceParseRequest, db: Session = Depends(get_db)):
    """
    Parse voice input AND execute the trade action.
    Supports: new_trade, close_trade, add_leg, modify_stop, modify_target.
    Returns the parsed result plus the created/updated trade.
    """
    parsed = parse_voice_text(payload.text)

    if not parsed.get("success"):
        return VoiceParseResponse(
            success=False,
            intent="unknown",
            raw_text=payload.text,
            notes=parsed.get("notes", payload.text),
        )

    intent = parsed["intent"]
    instrument_symbol = parsed.get("instrument", "")

    try:
        if intent == "new_trade":
            trade = await _execute_new_trade(db, parsed)
        elif intent == "close_trade":
            trade = await _execute_close_trade(db, parsed)
        elif intent == "add_leg":
            trade = await _execute_add_leg(db, parsed)
        elif intent == "modify_stop":
            trade = await _execute_modify_stop(db, parsed)
        elif intent == "modify_target":
            trade = await _execute_modify_target(db, parsed)
        else:
            return VoiceParseResponse(
                success=False,
                intent="unknown",
                raw_text=payload.text,
                notes=f"Unknown intent: {intent}",
            )

        db.refresh(trade)

        # Auto-set as active trade
        set_active(trade.id, instrument=instrument_symbol)

        return VoiceParseResponse(
            success=True,
            intent=intent,
            instrument=instrument_symbol,
            direction=parsed.get("direction"),
            volume=parsed.get("volume"),
            entry_price=parsed.get("entry_price"),
            close_price=parsed.get("close_price"),
            stop_price=parsed.get("stop_price"),
            target_price=parsed.get("target_price"),
            legs=[VoiceLeg(**leg) for leg in parsed.get("legs", [])],
            raw_text=payload.text,
            notes=None,
            trade=trade,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Voice trade execution failed")
        return VoiceParseResponse(
            success=False,
            intent=intent,
            raw_text=payload.text,
            notes=f"Execution error: {e}",
        )


# ---------------------------------------------------------------------------
# Execution helpers
# ---------------------------------------------------------------------------


async def _execute_new_trade(db: Session, parsed: dict) -> Trade:
    """Create a new trade from parsed voice input."""
    symbol = parsed.get("instrument", "")
    if not symbol:
        raise HTTPException(status_code=400, detail="No instrument symbol found in voice input")

    instr, _created = _resolve_instrument(db, symbol)
    direction = parsed.get("direction", "long")
    volume = parsed.get("volume", 1.0)
    entry_price = parsed.get("entry_price")
    if entry_price is None:
        raise HTTPException(status_code=400, detail="No entry price found in voice input")

    now = datetime.now(timezone.utc)

    trade = Trade(
        instrument_id=instr.id,
        symbol=instr.symbol,
        direction=direction,
        volume=volume,
        quantity=volume,
        entry_price=entry_price,
        entry_time=now,
        status="open",
    )
    db.add(trade)
    db.flush()

    # Create legs (stop and/or target)
    legs = parsed.get("legs", [])
    for leg in legs:
        leg_type = leg.get("type", "")
        leg_price = leg.get("price", 0)
        if leg_type == "stop":
            trade.stop_loss = leg_price
        elif leg_type == "target":
            trade.take_profit = leg_price

        db.add(TradeLeg(
            trade_id=trade.id,
            type=leg_type,
            price=leg_price,
            volume=volume,
            quantity=volume,
            timestamp=now,
            time=now,
        ))

    db.commit()
    await _broadcast_event("trade_created", trade)

    # Set active instrument context
    set_active_instrument(symbol)
    return trade


async def _execute_close_trade(db: Session, parsed: dict) -> Trade:
    """Close an open trade for the specified instrument."""
    symbol = parsed.get("instrument", "")
    if not symbol:
        raise HTTPException(status_code=400, detail="No instrument symbol found")

    trade = _find_open_trade(db, symbol)
    if not trade:
        raise HTTPException(
            status_code=404,
            detail=f"No open trade found for {symbol}",
        )

    close_price = parsed.get("close_price")
    if close_price:
        trade.exit_price = close_price

    trade.status = "closed"
    trade.exit_time = datetime.now(timezone.utc)

    # Compute PnL
    instr = db.query(Instrument).filter(Instrument.id == trade.instrument_id).first()
    if instr and trade.exit_price is not None:
        from app.routers.trades import _compute_pnl
        pnl, pnl_pct = _compute_pnl(trade, instr)
        trade.pnl = pnl
        trade.pnl_pct = pnl_pct

    db.commit()
    await _broadcast_event("trade_closed", trade)

    # Clear active trade if it was the one closed
    active_id = get_active()
    if active_id == trade.id:
        clear_active()

    return trade


async def _execute_add_leg(db: Session, parsed: dict) -> Trade:
    """Add a leg (add position) to an open trade for the instrument."""
    symbol = parsed.get("instrument", "")
    if not symbol:
        raise HTTPException(status_code=400, detail="No instrument symbol found")

    trade = _find_open_trade(db, symbol)
    if not trade:
        raise HTTPException(
            status_code=404,
            detail=f"No open trade found for {symbol}",
        )

    add_volume = parsed.get("volume", 1.0)
    add_price = parsed.get("entry_price")

    # Update main trade volume
    trade.volume = (trade.volume or 0) + add_volume
    trade.quantity = trade.volume

    now = datetime.now(timezone.utc)
    db.add(TradeLeg(
        trade_id=trade.id,
        type="add",
        price=add_price or trade.entry_price,
        volume=add_volume,
        quantity=add_volume,
        timestamp=now,
        time=now,
    ))

    db.commit()
    await _broadcast_event("trade_updated", trade)

    set_active(trade.id, instrument=symbol)
    return trade


async def _execute_modify_stop(db: Session, parsed: dict) -> Trade:
    """Modify the stop loss on an open trade."""
    symbol = parsed.get("instrument", "")
    if not symbol:
        raise HTTPException(status_code=400, detail="No instrument symbol found")

    trade = _find_open_trade(db, symbol)
    if not trade:
        raise HTTPException(
            status_code=404,
            detail=f"No open trade found for {symbol}",
        )

    stop_price = parsed.get("stop_price")
    if stop_price is None:
        raise HTTPException(status_code=400, detail="No stop price found")

    trade.stop_loss = stop_price
    now = datetime.now(timezone.utc)

    # Add a leg recording the modification
    db.add(TradeLeg(
        trade_id=trade.id,
        type="modify_stop",
        price=stop_price,
        volume=trade.volume,
        quantity=trade.volume,
        timestamp=now,
        time=now,
    ))

    db.commit()
    await _broadcast_event("trade_updated", trade)
    return trade


async def _execute_modify_target(db: Session, parsed: dict) -> Trade:
    """Modify the take profit on an open trade."""
    symbol = parsed.get("instrument", "")
    if not symbol:
        raise HTTPException(status_code=400, detail="No instrument symbol found")

    trade = _find_open_trade(db, symbol)
    if not trade:
        raise HTTPException(
            status_code=404,
            detail=f"No open trade found for {symbol}",
        )

    target_price = parsed.get("target_price")
    if target_price is None:
        raise HTTPException(status_code=400, detail="No target price found")

    trade.take_profit = target_price
    now = datetime.now(timezone.utc)

    db.add(TradeLeg(
        trade_id=trade.id,
        type="modify_target",
        price=target_price,
        volume=trade.volume,
        quantity=trade.volume,
        timestamp=now,
        time=now,
    ))

    db.commit()
    await _broadcast_event("trade_updated", trade)
    return trade


# ===========================================================================
# Active status endpoint (under /api/voice/active for voice context)
# ===========================================================================


@router.get("/active", response_model=ActiveTradeResponse)
def get_voice_active_status():
    """Get the active trade context for voice operations."""
    return get_active_trade_tracker().get_status()
