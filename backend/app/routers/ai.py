"""
AI-powered endpoints: trade debrief, auto-tagging, daily summary.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.ai_debrief import (
    analyze_trade,
    get_cached_debrief,
    auto_tag_trade,
    generate_daily_summary,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/debrief/{trade_id}")
async def create_debrief(trade_id: int, db: Session = Depends(get_db)):
    """
    Trigger an AI debrief for a trade.
    Uses local Ollama (qwen3.5:9b) to analyze the trade.
    """
    try:
        result = await analyze_trade(db, trade_id)
        return {"data": result, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=504, detail=str(e))
    except Exception as e:
        logger.exception("AI debrief failed for trade %d", trade_id)
        raise HTTPException(status_code=500, detail=f"AI analysis failed: {e}")


@router.get("/debrief/{trade_id}")
async def read_debrief(trade_id: int):
    """
    Get a cached AI debrief for a trade.
    Returns 404 if no cached debrief exists.
    """
    result = get_cached_debrief(trade_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No cached debrief found. POST to /api/ai/debrief/{trade_id} first.",
        )
    return {"data": result, "error": None}


@router.post("/auto-tag/{trade_id}")
async def create_auto_tags(trade_id: int, db: Session = Depends(get_db)):
    """
    AI suggests tags based on trade behavior.
    Returns a list of suggested tag names.
    """
    try:
        tags = await auto_tag_trade(db, trade_id)
        return {"data": tags, "error": None}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Auto-tag failed for trade %d", trade_id)
        raise HTTPException(status_code=500, detail=f"Auto-tag failed: {e}")


@router.post("/daily-summary")
async def create_daily_summary(
    date: str = None,
    db: Session = Depends(get_db),
):
    """
    Generate a summary of trades for a given date (default: today).
    Pass `?date=2025-01-15` to specify a date.
    """
    try:
        result = await generate_daily_summary(db, target_date=date)
        return {"data": result, "error": None}
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Daily summary failed")
        raise HTTPException(status_code=500, detail=f"Daily summary failed: {e}")
