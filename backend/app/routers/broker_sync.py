"""
Broker Sync Router — wire broker connectors to the journal database.

Endpoints:
  GET    /api/brokers           — list available brokers & connection status
  GET    /api/brokers/{name}/status  — check if a broker is connected
  POST   /api/brokers/{name}/sync   — sync a specific broker's trades
  POST   /api/brokers/sync-all       — sync all configured brokers
"""

import logging
import os
import sys
from datetime import date, datetime, timezone, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Trade, Instrument
from app.services.websocket_manager import manager

# Ensure project root is on sys.path for brokers/ package
_project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# Import broker connectors
from brokers import get_connector, list_connectors

logger = logging.getLogger("broker_sync")

router = APIRouter(prefix="/api/brokers", tags=["brokers"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class BrokerInfo(BaseModel):
    """Brief info about a registered broker connector."""
    name: str
    available: bool
    status: Optional[dict] = None
    last_sync: Optional[str] = None
    trade_count: int = 0


class BrokerStatus(BaseModel):
    """Connection status for a single broker."""
    name: str
    connected: bool
    details: dict


class SyncResult(BaseModel):
    """Result of a sync operation."""
    broker: str
    fetched: int
    imported: int
    skipped: int
    errors: list[str]
    duration_seconds: float


class SyncAllResult(BaseModel):
    """Result of syncing all brokers."""
    results: list[SyncResult]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_broker_config(name: str) -> dict:
    """
    Load broker-specific config from environment variables.

    Extends the config stored in settings so connectors can find their keys.
    """
    import os
    config = {}

    if name == "alpaca":
        config["api_key"] = os.environ.get("ALPACA_API_KEY", "")
        config["secret_key"] = os.environ.get("ALPACA_SECRET_KEY", "")
        config["paper"] = True  # default to paper; override if needed
    elif name == "ibkr":
        config["host"] = os.environ.get("IBKR_HOST", "127.0.0.1")
        config["port"] = int(os.environ.get("IBKR_PORT", "7497"))
        config["client_id"] = int(os.environ.get("IBKR_CLIENT_ID", "1"))
    elif name == "ctrader":
        config["client_id"] = os.environ.get("CTRADER_CLIENT_ID", "")
        config["client_secret"] = os.environ.get("CTRADER_CLIENT_SECRET", "")
    elif name == "schwab":
        config["app_key"] = os.environ.get("SCHWAB_APP_KEY", "")
        config["app_secret"] = os.environ.get("SCHWAB_APP_SECRET", "")

    return config


def _lookup_or_create_instrument(db: Session, symbol: str, broker: str) -> Optional[Instrument]:
    """Find an instrument by symbol, or create one if it doesn't exist."""
    if not symbol:
        return None

    instr = db.query(Instrument).filter(
        Instrument.symbol.ilike(symbol)
    ).first()

    if instr:
        return instr

    # Auto-create with reasonable defaults based on broker
    asset_class = "stock"
    if "." in symbol:
        # Could be forex or crypto
        if "/" in symbol:
            asset_class = "forex"
        else:
            asset_class = "crypto"

    instr = Instrument(
        symbol=symbol.upper(),
        name=symbol.upper(),
        asset_class=asset_class,
        point_value=1.0,
        tick_size=0.01,
    )
    db.add(instr)
    db.flush()
    logger.info("Auto-created instrument '%s' (class=%s)", symbol, asset_class)
    return instr


def _canonical_to_trade_dict(normalized: dict, instrument_id: int) -> dict:
    """Map canonical broker trade dict to Trade model fields."""
    # Parse times
    entry_time = None
    if normalized.get("entry_time"):
        try:
            entry_time = datetime.fromisoformat(normalized["entry_time"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            entry_time = datetime.now(timezone.utc)

    exit_time = None
    if normalized.get("exit_time"):
        try:
            exit_time = datetime.fromisoformat(normalized["exit_time"].replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    return {
        "instrument_id": instrument_id,
        "symbol": normalized.get("instrument", "").upper(),
        "direction": normalized.get("direction", "long"),
        "volume": float(normalized.get("volume", 0)),
        "quantity": float(normalized.get("volume", 0)),
        "entry_price": float(normalized.get("entry_price", 0)),
        "exit_price": float(normalized["exit_price"]) if normalized.get("exit_price") is not None else None,
        "entry_time": entry_time,
        "exit_time": exit_time,
        "pnl": float(normalized["pnl"]) if normalized.get("pnl") is not None else None,
        "pnl_pct": float(normalized["pnl_pct"]) if normalized.get("pnl_pct") is not None else None,
        "commission": float(normalized.get("commission", 0)),
        "fees": float(normalized.get("commission", 0)),
        "status": normalized.get("status", "closed"),
        "strategy_tag": normalized.get("strategy_tag", ""),
        "strategy": normalized.get("strategy_tag", ""),
        "broker": normalized.get("broker", ""),
        "notes": normalized.get("notes", ""),
    }


def _get_trade_count_for_broker(db: Session, broker_name: str) -> int:
    """Count trades already imported for a given broker."""
    return db.query(Trade).filter(Trade.broker == broker_name).count()


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[BrokerInfo])
def list_brokers(db: Session = Depends(get_db)):
    """List all registered brokers with their connection status and trade count."""
    available = list_connectors()
    result = []

    for name in available:
        config = _load_broker_config(name)
        connector = get_connector(name, config)
        status = None
        if connector and hasattr(connector, "check_connection"):
            try:
                status = connector.check_connection()
            except Exception as e:
                status = {"connected": False, "error": str(e)}

        trade_count = _get_trade_count_for_broker(db, name)

        result.append(BrokerInfo(
            name=name,
            available=True,
            status=status,
            last_sync=None,  # TODO: persist last sync time
            trade_count=trade_count,
        ))

    # Also include brokers that are registered but maybe not available
    for name in list_connectors():
        if name not in [b.name for b in result]:
            result.append(BrokerInfo(name=name, available=True, trade_count=0))

    return result


@router.get("/{name}/status", response_model=BrokerStatus)
def broker_status(name: str):
    """Check if a specific broker is connected and reachable."""
    if name not in list_connectors():
        raise HTTPException(
            status_code=404,
            detail=f"Broker '{name}' not registered. Available: {', '.join(list_connectors())}",
        )

    config = _load_broker_config(name)
    connector = get_connector(name, config)
    if not connector:
        raise HTTPException(status_code=500, detail=f"Could not instantiate connector '{name}'")

    try:
        if hasattr(connector, "check_connection"):
            details = connector.check_connection()
        else:
            # Fallback: try to get account summary
            summary = connector.get_account_summary()
            details = {"connected": bool(summary), "summary": summary if summary else "empty"}

        return BrokerStatus(
            name=name,
            connected=bool(details.get("connected", False)),
            details=details,
        )
    except Exception as e:
        return BrokerStatus(name=name, connected=False, details={"error": str(e)})


@router.post("/{name}/sync", response_model=SyncResult)
async def sync_broker(
    name: str,
    days: int = Query(30, description="Number of days of history to fetch"),
    db: Session = Depends(get_db),
):
    """
    Sync trades from a specific broker.

    1. Connects to the broker
    2. Fetches trades (last N days)
    3. For each trade, looks up or creates the instrument
    4. Creates/updates the trade in the database
    5. Broadcasts via WebSocket
    6. Returns import counts
    """
    if name not in list_connectors():
        raise HTTPException(
            status_code=404,
            detail=f"Broker '{name}' not registered. Available: {', '.join(list_connectors())}",
        )

    start_time = datetime.now(timezone.utc)
    config = _load_broker_config(name)
    connector = get_connector(name, config)

    if not connector:
        raise HTTPException(status_code=500, detail=f"Failed to initialize connector '{name}'")

    # Calculate date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Fetch trades from broker
    logger.info("Syncing %s trades from %s to %s", name, start_date, end_date)
    try:
        raw_trades = connector.fetch_trades(start_date=start_date, end_date=end_date)
    except Exception as e:
        logger.error("Error fetching trades from %s: %s", name, e)
        raise HTTPException(status_code=502, detail=f"Error fetching trades: {str(e)}")

    if not raw_trades:
        return SyncResult(
            broker=name,
            fetched=0,
            imported=0,
            skipped=0,
            errors=[],
            duration_seconds=(datetime.now(timezone.utc) - start_time).total_seconds(),
        )

    # Import trades into database
    imported = 0
    skipped = 0
    errors = []

    for raw in raw_trades:
        try:
            # Look up or create instrument
            symbol = raw.get("instrument", "")
            instr = _lookup_or_create_instrument(db, symbol, name)
            if instr is None and symbol:
                errors.append(f"No instrument for symbol '{symbol}'")
                continue
            elif instr is None:
                errors.append("Trade has no instrument symbol, skipping")
                continue

            # Check for existing trade by broker_trade_id
            broker_trade_id = raw.get("broker_trade_id", "")
            existing = None
            if broker_trade_id:
                existing = db.query(Trade).filter(
                    Trade.broker == name,
                    Trade.notes.contains(f"broker_id:{broker_trade_id}")
                ).first()

            if existing:
                skipped += 1
                continue

            # Map to trade model
            trade_data = _canonical_to_trade_dict(raw, instr.id)

            # Store broker ID in notes for dedup
            notes = trade_data.get("notes", "") or ""
            if broker_trade_id:
                note_tag = f" [broker_id:{broker_trade_id}]"
                if note_tag not in notes:
                    notes += note_tag
                trade_data["notes"] = notes.strip()

            trade = Trade(**trade_data)
            db.add(trade)
            db.flush()

            # Broadcast via WebSocket
            try:
                await manager.broadcast({
                    "type": "trade_created",
                    "data": {
                        "id": trade.id,
                        "instrument_id": trade.instrument_id,
                        "instrument_symbol": symbol.upper(),
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
                        "created_at": trade.created_at.isoformat() if trade.created_at else None,
                    },
                })
            except Exception as ws_err:
                logger.warning("WebSocket broadcast failed during sync: %s", ws_err)

            imported += 1

        except Exception as e:
            logger.error("Error importing trade from %s: %s", name, e)
            errors.append(str(e))

    # Final commit
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("DB commit failed during broker sync: %s", e)
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    duration = (datetime.now(timezone.utc) - start_time).total_seconds()
    logger.info(
        "Sync %s complete: %d fetched, %d imported, %d skipped, %d errors in %.2fs",
        name, len(raw_trades), imported, skipped, len(errors), duration,
    )

    return SyncResult(
        broker=name,
        fetched=len(raw_trades),
        imported=imported,
        skipped=skipped,
        errors=errors[:20],  # Limit error detail
        duration_seconds=round(duration, 2),
    )


@router.post("/sync-all", response_model=SyncAllResult)
async def sync_all_brokers(
    days: int = Query(30, description="Number of days of history to fetch"),
    db: Session = Depends(get_db),
):
    """Sync trades from all registered brokers sequentially."""
    results = []
    for name in list_connectors():
        try:
            result = await sync_broker(name, days=days, db=db)
            results.append(result)
        except HTTPException as e:
            results.append(SyncResult(
                broker=name,
                fetched=0,
                imported=0,
                skipped=0,
                errors=[e.detail],
                duration_seconds=0,
            ))
        except Exception as e:
            results.append(SyncResult(
                broker=name,
                fetched=0,
                imported=0,
                skipped=0,
                errors=[str(e)],
                duration_seconds=0,
            ))

    return SyncAllResult(results=results)
