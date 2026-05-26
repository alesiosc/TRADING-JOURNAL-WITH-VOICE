from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Trade, TradeLeg, Instrument, Tag, TradeTag
from app.services.import_service import parse_csv

router = APIRouter(prefix="/api/import", tags=["import"])


class ImportPreview(BaseModel):
    """Response model for CSV preview."""
    total_rows: int
    success_count: int
    error_count: int
    rows: list
    errors: list
    detected_format: Optional[str] = None


class ImportConfirmRequest(BaseModel):
    """Request model for confirming an import."""
    rows: List[int]  # indices of rows in the preview to import (0-based)


class ImportConfirmResponse(BaseModel):
    """Response model for confirmed import."""
    imported_count: int
    error_count: int
    errors: list


@router.post("/csv", response_model=ImportPreview)
async def preview_csv(
    file: UploadFile = File(...),
    dry_run: bool = Query(True, description="If true, only preview without saving"),
    use_normalizer: bool = Query(False, description="Use brokers/csv_normalizer.py for format detection"),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV file and parse it.

    By default (dry_run=true), returns a preview without saving to DB.
    Set dry_run=false to preview AND save immediately.

    Set use_normalizer=true to use brokers/csv_normalizer.py which supports
    NinjaTrader 8, MetaTrader 4/5, Quantower, and generic CSV formats.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    raw = await file.read()
    try:
        content = raw.decode("utf-8-sig")  # handles BOM
    except UnicodeDecodeError:
        try:
            content = raw.decode("latin-1")
        except Exception:
            raise HTTPException(status_code=400, detail="Could not decode CSV file")

    detected_format = None

    if use_normalizer:
        # Use brokers/csv_normalizer.py for broker-specific format detection
        try:
            from brokers.csv_normalizer import CsvNormalizer, normalize_csv

            # Save to temp file for normalizer
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False, encoding="utf-8"
            ) as f:
                f.write(content)
                temp_path = f.name

            try:
                normalizer = CsvNormalizer()
                detected_format = normalizer.detect_format(temp_path)
                parsed = normalizer.parse(temp_path)

                # Convert normalized trades to our format
                success = []
                errors = []
                for i, td in enumerate(parsed):
                    try:
                        # Look up or create instrument
                        symbol = td.get("instrument", td.get("symbol", ""))
                        if not symbol:
                            errors.append({"row": i + 1, "reason": "Missing symbol"})
                            continue

                        instr = db.query(Instrument).filter(Instrument.symbol == symbol).first()
                        if not instr:
                            instr = Instrument(symbol=symbol, name=symbol)
                            db.add(instr)
                            db.flush()

                        trade_dict = {
                            "instrument_id": instr.id,
                            "symbol": symbol,
                            "direction": td.get("direction", "long"),
                            "volume": td.get("volume", td.get("quantity", 1.0)),
                            "entry_price": td["entry_price"],
                            "exit_price": td.get("exit_price"),
                            "entry_time": td.get("entry_time", datetime.utcnow().isoformat()),
                            "exit_time": td.get("exit_time"),
                            "pnl": td.get("pnl"),
                            "commission": td.get("commission", 0.0),
                            "status": td.get("status", "closed"),
                            "strategy_tag": td.get("strategy_tag", ""),
                            "strategy": td.get("strategy_tag", ""),
                            "broker": td.get("broker", "csv"),
                            "notes": td.get("notes", ""),
                            "fees": td.get("commission", 0.0),
                        }
                        success.append(trade_dict)
                    except Exception as e:
                        errors.append({"row": i + 1, "reason": str(e)})

                if not dry_run and success:
                    saved = _save_trades(success, db)
                    return ImportPreview(
                        total_rows=len(success) + len(errors),
                        success_count=len(saved),
                        error_count=len(errors),
                        rows=saved,
                        errors=errors,
                        detected_format=detected_format,
                    )

                return ImportPreview(
                    total_rows=len(success) + len(errors),
                    success_count=len(success),
                    error_count=len(errors),
                    rows=success,
                    errors=errors,
                    detected_format=detected_format,
                )
            finally:
                os.unlink(temp_path)
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="brokers.csv_normalizer not available. Check that brokers/ is in Python path.",
            )
    else:
        # Use existing import_service parser (simpler, generic)
        result = parse_csv(content, db)

        if not dry_run and result["success"]:
            saved = _save_trades(result["success"], db)
            return ImportPreview(
                total_rows=len(result["success"]) + len(result["errors"]),
                success_count=len(saved),
                error_count=len(result["errors"]),
                rows=saved,
                errors=result["errors"],
                detected_format="generic",
            )

        return ImportPreview(
            total_rows=len(result["success"]) + len(result["errors"]),
            success_count=len(result["success"]),
            error_count=len(result["errors"]),
            rows=result["success"],
            errors=result["errors"],
            detected_format="generic",
        )


@router.post("/csv/confirm", response_model=ImportConfirmResponse)
def confirm_csv_import(
    payload: ImportConfirmRequest,
    db: Session = Depends(get_db),
):
    """
    Confirm import of previously previewed rows.

    Accepts a list of row indices (0-based from a preview response)
    and saves those trades to the database.
    NOTE: This is a simplified endpoint. For a full flow, the frontend
    should pass the actual trade data, not indices. We keep preview data
    in memory via the request body approach.
    """
    raise HTTPException(
        status_code=501,
        detail="Direct confirm by index not supported. Use POST /api/import/csv with dry_run=false to import directly, "
               "or pass the rows directly in the request body.",
    )


def _save_trades(trade_dicts: list, db: Session) -> list:
    """Save trade dicts to the database and return the created trades as dicts."""
    saved = []
    for td in trade_dicts:
        tags_data = td.pop("_tags", None)

        trade = Trade(
            instrument_id=td["instrument_id"],
            symbol=td.get("symbol"),
            direction=td.get("direction", "long"),
            volume=td.get("volume", 1.0),
            quantity=td.get("volume", td.get("quantity")),
            entry_price=td["entry_price"],
            exit_price=td.get("exit_price"),
            stop_loss=td.get("stop_loss"),
            take_profit=td.get("take_profit"),
            entry_time=td.get("entry_time", datetime.utcnow()),
            exit_time=td.get("exit_time"),
            pnl=td.get("pnl"),
            pnl_pct=td.get("pnl_pct"),
            fees=td.get("fees", td.get("commission", 0.0)),
            commission=td.get("commission", 0.0),
            status=td.get("status", "open"),
            setup_type=td.get("setup_type"),
            strategy=td.get("strategy", td.get("strategy_tag")),
            strategy_tag=td.get("strategy_tag"),
            broker=td.get("broker", "csv"),
            account_id=td.get("account_id"),
            notes=td.get("notes"),
            rating=td.get("rating"),
        )
        db.add(trade)
        db.flush()

        # Handle tags (SL, TP, etc.)
        if tags_data:
            for tag_name in tags_data:
                tag = db.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.add(tag)
                    db.flush()
                existing = db.query(TradeTag).filter(
                    TradeTag.trade_id == trade.id,
                    TradeTag.tag_id == tag.id,
                ).first()
                if not existing:
                    db.add(TradeTag(trade_id=trade.id, tag_id=tag.id))

        db.flush()
        db.refresh(trade)
        saved.append(_trade_to_dict(trade))
    db.commit()
    return saved


def _trade_to_dict(trade: Trade) -> dict:
    """Convert a trade ORM object to a plain dict for JSON response."""
    instr_symbol = trade.instrument.symbol if trade.instrument else trade.symbol
    return {
        "id": trade.id,
        "instrument_id": trade.instrument_id,
        "symbol": instr_symbol,
        "direction": trade.direction,
        "volume": trade.volume,
        "quantity": trade.quantity,
        "entry_price": trade.entry_price,
        "exit_price": trade.exit_price,
        "stop_loss": trade.stop_loss,
        "take_profit": trade.take_profit,
        "entry_time": trade.entry_time.isoformat() if trade.entry_time else None,
        "exit_time": trade.exit_time.isoformat() if trade.exit_time else None,
        "pnl": trade.pnl,
        "pnl_pct": trade.pnl_pct,
        "fees": trade.fees or trade.commission,
        "commission": trade.commission,
        "status": trade.status,
        "setup_type": trade.setup_type,
        "strategy": trade.strategy or trade.strategy_tag,
        "strategy_tag": trade.strategy_tag,
        "broker": trade.broker,
        "account_id": trade.account_id,
        "notes": trade.notes,
        "rating": trade.rating,
    }
