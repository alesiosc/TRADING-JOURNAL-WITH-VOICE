"""
NT8 Integration Router — receives trade data from NinjaTrader 8.

Endpoints:
  POST /api/nt8/trade     — Receive trade event (entry/exit/modify/partial)
  POST /api/nt8/screenshot — Manual screenshot trigger from NT8
  GET  /api/nt8/status     — Integration health check
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.services import nt8_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nt8", tags=["nt8"])


class NT8TradeRequest(BaseModel):
    event: str = "entry"  # entry | exit | full_close | modify | partial_close
    symbol: str
    direction: str = "long"
    quantity: float = 1.0
    entry_price: float = 0.0
    exit_price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    fill_time: str | None = None
    account: str = "Sim101"
    trade_id: str = ""
    note: str = ""
    capture_screenshot: bool = True


class NT8ScreenshotRequest(BaseModel):
    trade_id: int | None = None
    event: str = "manual"


@router.post("/trade")
async def receive_trade(payload: NT8TradeRequest, db: Session = Depends(get_db)):
    """Receive a trade event from an NT8 indicator."""
    try:
        result = nt8_service.process_nt8_trade(payload.model_dump(), db)

        # Auto-trigger screenshot on entry/exit/modify
        if result.get("success") and payload.capture_screenshot:
            trade_id = result.get("trade_id")
            if trade_id:
                screenshot_result = nt8_service.trigger_screenshot(trade_id, payload.event)
                result["screenshot"] = screenshot_result

        return result
    except Exception as e:
        logger.error(f"NT8 trade processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/screenshot")
async def trigger_screenshot(payload: NT8ScreenshotRequest):
    """Trigger a screenshot capture from NT8."""
    result = nt8_service.trigger_screenshot(payload.trade_id, payload.event)
    return result


@router.get("/status")
async def nt8_status():
    """Check NT8 integration status."""
    return {
        "status": "ok",
        "version": "1.0.0",
        "endpoints": {
            "trade": "POST /api/nt8/trade",
            "screenshot": "POST /api/nt8/screenshot",
            "status": "GET /api/nt8/status",
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
