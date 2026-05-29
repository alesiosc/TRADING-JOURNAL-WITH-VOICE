"""
NT8 Integration Service — processes incoming trade data from NinjaTrader 8.

Handles:
  - New trade entries (long/short) → creates trade in DB
  - Trade modifications (SL, TP, BE) → updates trade
  - Partial closes → creates trade legs
  - Full closes → closes trade, auto-calculates P&L
  - Auto-screenshot triggering on all events
"""

import logging
import os
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Trade, TradeLeg, Instrument, JournalEntry
from app.config import settings

logger = logging.getLogger(__name__)


def resolve_instrument(symbol: str, db: Session) -> Optional[Instrument]:
    """Find or create an instrument by symbol."""
    sym = symbol.strip().upper()
    instr = db.query(Instrument).filter(Instrument.symbol == sym).first()
    if instr:
        return instr

    # Auto-create with sensible defaults
    asset_class = "futures"
    point_value = 50.0
    tick_size = 0.25

    # Common futures point values
    FUTURES_MAP = {
        "ES": (50.0, 0.25), "NQ": (20.0, 0.25), "YM": (5.0, 1.0),
        "RTY": (50.0, 0.10), "CL": (1000.0, 0.01), "GC": (100.0, 0.10),
        "SI": (5000.0, 0.005), "HG": (25000.0, 0.0005), "ZB": (1000.0, 0.03125),
        "ZN": (1000.0, 0.015625), "ZF": (1000.0, 0.0078125), "ZT": (2000.0, 0.00390625),
        "6E": (125000.0, 0.00005), "6J": (12500000.0, 0.0000005),
    }
    if sym in FUTURES_MAP:
        point_value, tick_size = FUTURES_MAP[sym]

    instr = Instrument(
        symbol=sym,
        name=sym,
        asset_class=asset_class,
        point_value=point_value,
        tick_size=tick_size,
    )
    db.add(instr)
    db.commit()
    db.refresh(instr)
    return instr


def process_nt8_trade(data: dict, db: Session) -> dict:
    """
    Process an incoming trade event from NT8.

    Expected payload:
    {
        "event": "entry" | "exit" | "modify" | "partial_close",
        "symbol": "ES",
        "direction": "long" | "short",
        "quantity": 2,
        "entry_price": 5245.50,
        "exit_price": 5278.25,       # on exit events
        "stop_loss": 5238.00,        # current SL
        "take_profit": 5300.00,      # current TP
        "fill_time": "2026-05-29T14:30:00Z",
        "account": "Sim101",
        "trade_id": "nt8-abc123",    # NT8's internal order/position ID
        "note": "optional note"
    }
    """
    event = data.get("event", "entry")
    symbol = data.get("symbol", "").strip().upper()
    direction = data.get("direction", "long")
    quantity = float(data.get("quantity", 1))
    entry_price = float(data.get("entry_price", 0))
    exit_price = data.get("exit_price")
    if exit_price is not None:
        exit_price = float(exit_price)
    stop_loss = data.get("stop_loss")
    if stop_loss is not None:
        stop_loss = float(stop_loss)
    take_profit = data.get("take_profit")
    if take_profit is not None:
        take_profit = float(take_profit)
    fill_time = data.get("fill_time")
    if fill_time:
        try:
            fill_time = datetime.fromisoformat(fill_time.replace("Z", "+00:00"))
        except Exception:
            fill_time = datetime.now(timezone.utc)
    else:
        fill_time = datetime.now(timezone.utc)

    account = data.get("account", "NT8")
    nt8_trade_id = data.get("trade_id", "")
    note = data.get("note", "")

    # Resolve instrument
    instr = resolve_instrument(symbol, db)
    if not instr:
        return {"success": False, "error": f"Could not resolve instrument: {symbol}"}

    # Look for an existing open trade from NT8 (by nt8_trade_id or symbol+direction)
    open_trade = None
    if nt8_trade_id:
        open_trade = db.query(Trade).filter(
            Trade.broker == "NT8",
            Trade.account_id == account,
            Trade.status == "open"
        ).order_by(Trade.id.desc()).first()

    if event == "entry":
        # Create new trade
        trade = Trade(
            instrument_id=instr.id,
            symbol=symbol,
            direction=direction,
            quantity=quantity,
            volume=quantity,
            entry_price=entry_price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            entry_time=fill_time,
            status="open",
            setup_type="NT8",
            broker="NT8",
            account_id=account,
            notes=note,
        )
        db.add(trade)
        db.commit()
        db.refresh(trade)

        # Add entry leg
        leg = TradeLeg(
            trade_id=trade.id,
            type="entry",
            price=entry_price,
            quantity=quantity,
            volume=quantity,
            timestamp=fill_time,
            time=fill_time,
        )
        db.add(leg)
        db.commit()

        # Journal entry
        _add_journal(trade.id, f"NT8 entry: {direction} {quantity} {symbol} @ {entry_price}", "neutral", db)

        return {"success": True, "trade_id": trade.id, "event": "entry"}

    elif event in ("exit", "full_close"):
        # Find and close the open trade
        trade = _find_open_nt8_trade(db, symbol, direction, account, nt8_trade_id)
        if not trade:
            # Create as a closed trade if we missed the entry
            trade = Trade(
                instrument_id=instr.id,
                symbol=symbol,
                direction=direction,
                quantity=quantity,
                volume=quantity,
                entry_price=entry_price or 0,
                exit_price=exit_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                entry_time=fill_time,
                exit_time=fill_time,
                status="closed",
                setup_type="NT8",
                broker="NT8",
                account_id=account,
                notes=note or "NT8 exit (missed entry)",
            )
            db.add(trade)
            db.commit()
            db.refresh(trade)
            _add_journal(trade.id, f"NT8 exit (no prior entry): {symbol}", "neutral", db)
            return {"success": True, "trade_id": trade.id, "event": "exit"}

        # Close the trade
        trade.exit_price = exit_price
        trade.exit_time = fill_time
        trade.status = "closed"
        trade.stop_loss = stop_loss or trade.stop_loss
        trade.take_profit = take_profit or trade.take_profit
        trade.notes = (trade.notes or "") + f" | {note}" if note else trade.notes

        # Auto-calculate P&L
        _calc_pnl(trade, instr)
        db.commit()

        # Add exit leg
        leg = TradeLeg(
            trade_id=trade.id,
            type="exit",
            price=exit_price or 0,
            quantity=trade.quantity or trade.volume or quantity,
            volume=trade.volume or quantity,
            timestamp=fill_time,
            time=fill_time,
        )
        db.add(leg)
        db.commit()

        _add_journal(trade.id, f"NT8 close: {symbol} @ {exit_price} | P&L: ${trade.pnl:.2f}", "positive" if (trade.pnl or 0) > 0 else "negative", db)

        return {"success": True, "trade_id": trade.id, "event": "exit", "pnl": trade.pnl}

    elif event == "modify":
        trade = _find_open_nt8_trade(db, symbol, direction, account, nt8_trade_id)
        if not trade:
            return {"success": False, "error": "No open trade found to modify"}

        if stop_loss is not None and stop_loss != trade.stop_loss:
            old_sl = trade.stop_loss
            trade.stop_loss = stop_loss
            _add_leg(trade.id, "modify", stop_loss, quantity, fill_time, db)
            _add_journal(trade.id, f"SL moved: {old_sl} → {stop_loss}", "neutral", db)

        if take_profit is not None and take_profit != trade.take_profit:
            trade.take_profit = take_profit
            _add_journal(trade.id, f"TP updated: {take_profit}", "neutral", db)

        if entry_price and entry_price != trade.entry_price:
            # Breakeven adjustment or partial
            old_entry = trade.entry_price
            trade.entry_price = entry_price
            _add_journal(trade.id, f"Entry adjusted: {old_entry} → {entry_price}" + (" (BE)" if direction == "long" and entry_price >= trade.stop_loss else ""), "confident", db)

        db.commit()

        return {"success": True, "trade_id": trade.id, "event": "modify"}

    elif event == "partial_close":
        trade = _find_open_nt8_trade(db, symbol, direction, account, nt8_trade_id)
        if not trade:
            return {"success": False, "error": "No open trade found for partial close"}

        partial_qty = float(data.get("partial_quantity", quantity))
        _add_leg(trade.id, "reduce", exit_price or 0, partial_qty, fill_time, db)
        trade.quantity = (trade.quantity or trade.volume or 0) - partial_qty
        if trade.quantity <= 0:
            trade.status = "closed"
            trade.exit_price = exit_price
            trade.exit_time = fill_time
            _calc_pnl(trade, instr)

        db.commit()
        _add_journal(trade.id, f"Partial close: {partial_qty} {symbol} @ {exit_price}", "neutral", db)

        return {"success": True, "trade_id": trade.id, "event": "partial_close"}

    return {"success": False, "error": f"Unknown event: {event}"}


def trigger_screenshot(trade_id: int, event: str = "entry") -> dict:
    """Trigger a screenshot capture via the screenshot module."""
    try:
        from app.routers.screenshots import get_screenshot_module
        mod = get_screenshot_module()
        if mod is None:
            return {"success": False, "error": "Screenshot module not loaded"}

        result = mod.capture(trade_id=trade_id, event=event)
        if result is None:
            return {"success": False, "error": "Screenshot capture failed"}

        return {"success": True, "path": result.get("url_path", "")}
    except Exception as e:
        logger.warning(f"Screenshot trigger failed: {e}")
        return {"success": False, "error": str(e)}


# ── Helpers ──

def _find_open_nt8_trade(db, symbol, direction, account, nt8_id=None):
    """Find the most recent open trade matching NT8 criteria."""
    query = db.query(Trade).filter(
        Trade.broker == "NT8",
        Trade.symbol == symbol,
        Trade.status == "open"
    )
    if account:
        query = query.filter(Trade.account_id == account)
    if direction:
        query = query.filter(Trade.direction == direction)
    return query.order_by(Trade.id.desc()).first()


def _calc_pnl(trade, instr):
    """Auto-calculate P&L from entry/exit prices."""
    if trade.entry_price and trade.exit_price:
        multiplier = 1 if trade.direction == "long" else -1
        raw_diff = (trade.exit_price - trade.entry_price) * multiplier
        trade.pnl = round(raw_diff * (trade.volume or 1) * (instr.point_value or 1), 2)
        trade.pnl_pct = round(
            ((trade.exit_price - trade.entry_price) / trade.entry_price * 100) * multiplier,
            2
        )


def _add_leg(trade_id, typ, price, qty, timestamp, db):
    leg = TradeLeg(
        trade_id=trade_id, type=typ, price=price,
        quantity=qty, volume=qty, timestamp=timestamp, time=timestamp,
    )
    db.add(leg)


def _add_journal(trade_id, content, sentiment, db):
    entry = JournalEntry(
        trade_id=trade_id,
        content=content,
        sentiment=sentiment,
        created_at=datetime.now(timezone.utc),
    )
    db.add(entry)
