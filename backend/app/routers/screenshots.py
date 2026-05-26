import os
import shutil
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Screenshot
from app.schemas import ScreenshotCreate, ScreenshotRead, ScreenshotUpdate
from app.services.websocket_manager import manager
from app.config import settings

router = APIRouter(prefix="/api/screenshots", tags=["screenshots"])

# Upload directory for screenshots
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "screenshots")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Lazy-loaded screenshot module reference
# Set by app.main during startup via configure_screenshot_module()
# ---------------------------------------------------------------------------
_screenshot_module = None


def configure_screenshot_module(module):
    """Inject the ScreenshotModule instance (called from app.main)."""
    global _screenshot_module
    _screenshot_module = module


def get_screenshot_module():
    """Return the injected module or None."""
    return _screenshot_module


async def _broadcast_screenshot(ss: Screenshot):
    """Broadcast a screenshot event to all WebSocket clients."""
    await manager.broadcast({
        "type": "screenshot_added",
        "data": {
            "id": ss.id,
            "trade_id": ss.trade_id,
            "type": ss.type,
            "file_path": ss.file_path,
            "thumbnail_path": ss.thumbnail_path,
            "trigger_event": ss.trigger_event,
            "auto_captured": ss.auto_captured,
            "captured_at": ss.captured_at.isoformat() if ss.captured_at else None,
        },
    })


async def _save_screenshot_record(
    file_path_rel: str,
    trade_id: Optional[int] = None,
    type_: str = "manual",
    trigger_event: Optional[str] = None,
    auto_captured: bool = False,
    db: Session = None,
):
    """Create a Screenshot DB record and broadcast via WebSocket."""
    ss = Screenshot(
        trade_id=trade_id,
        type=type_,
        file_path=file_path_rel,
        trigger_event=trigger_event,
        auto_captured=auto_captured,
    )
    db.add(ss)
    db.commit()
    db.refresh(ss)
    await _broadcast_screenshot(ss)
    return ss


# =========================================================================
# Existing endpoints
# =========================================================================

@router.get("/", response_model=List[ScreenshotRead])
def list_screenshots(
    trade_id: int = Query(None, description="Filter by trade"),
    type: str = Query(None, description="Filter by type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Screenshot)
    if trade_id is not None:
        query = query.filter(Screenshot.trade_id == trade_id)
    if type:
        query = query.filter(Screenshot.type == type)
    return query.order_by(Screenshot.captured_at.desc()).offset(skip).limit(limit).all()


@router.get("/{screenshot_id}", response_model=ScreenshotRead)
def get_screenshot(screenshot_id: int, db: Session = Depends(get_db)):
    ss = db.query(Screenshot).filter(Screenshot.id == screenshot_id).first()
    if not ss:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    return ss


@router.post("/", response_model=ScreenshotRead, status_code=201)
async def create_screenshot(
    trade_id: int = Form(...),
    type: str = Form("manual"),
    trigger_event: str = Form(None),
    auto_captured: bool = Form(False),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # Save the uploaded file
    file_ext = os.path.splitext(file.filename or ".png")[1] or ".png"
    import uuid
    filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Create relative URL path
    url_path = f"/uploads/screenshots/{filename}"

    ss = await _save_screenshot_record(
        file_path_rel=url_path,
        trade_id=trade_id,
        type_=type,
        trigger_event=trigger_event,
        auto_captured=auto_captured,
        db=db,
    )
    return ss


# =========================================================================
# NEW: Manual & auto-capture endpoints (using screenshot module)
# =========================================================================

@router.post("/capture", response_model=ScreenshotRead, status_code=201)
async def manual_capture(
    trade_id: int = Form(None),
    type: str = Form("manual"),
    db: Session = Depends(get_db),
):
    """Trigger a manual screenshot capture using the screenshot module.

    Captures the screen immediately based on the configured capture_mode
    (active_monitor or specific monitor). Saves to uploads/screenshots/
    and creates a DB record.
    """
    mod = get_screenshot_module()
    if mod is None:
        raise HTTPException(status_code=503, detail="Screenshot module not initialized")

    result = mod.capture(trade_id=trade_id, event="manual")
    if result is None:
        raise HTTPException(status_code=500, detail="Screenshot capture failed")

    url_path = result["url_path"]

    ss = await _save_screenshot_record(
        file_path_rel=url_path,
        trade_id=trade_id,
        type_=type,
        trigger_event="manual",
        auto_captured=False,
        db=db,
    )
    return ss


@router.post("/auto-capture/{trade_id}", response_model=ScreenshotRead, status_code=201)
async def auto_capture(
    trade_id: int,
    event: str = Query("entry", description="Trigger event: entry, exit, sl_move, add, modification"),
    db: Session = Depends(get_db),
):
    """Auto-capture a screenshot for a trade event.

    Only captures if auto_capture_on_events is enabled in config.yaml.
    Supported events: entry, exit, sl_move, add, modification.
    """
    valid_events = {"entry", "exit", "sl_move", "add", "modification"}
    if event not in valid_events:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid event '{event}'. Must be one of: {', '.join(sorted(valid_events))}",
        )

    mod = get_screenshot_module()
    if mod is None:
        raise HTTPException(status_code=503, detail="Screenshot module not initialized")

    # Check auto-capture is enabled
    if not mod.config.get("auto_capture_on_events", True):
        raise HTTPException(status_code=400, detail="Auto-capture is disabled in config.yaml")

    result = mod.capture(trade_id=trade_id, event=event)
    if result is None:
        raise HTTPException(status_code=500, detail="Screenshot capture failed")

    url_path = result["url_path"]

    ss = await _save_screenshot_record(
        file_path_rel=url_path,
        trade_id=trade_id,
        type_=f"auto_{event}",
        trigger_event=event,
        auto_captured=True,
        db=db,
    )
    return ss


# =========================================================================
# Standard CRUD
# =========================================================================

@router.put("/{screenshot_id}", response_model=ScreenshotRead)
def update_screenshot(screenshot_id: int, payload: ScreenshotUpdate, db: Session = Depends(get_db)):
    ss = db.query(Screenshot).filter(Screenshot.id == screenshot_id).first()
    if not ss:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(ss, field, value)
    db.commit()
    db.refresh(ss)
    return ss


@router.delete("/{screenshot_id}", status_code=204)
def delete_screenshot(screenshot_id: int, db: Session = Depends(get_db)):
    ss = db.query(Screenshot).filter(Screenshot.id == screenshot_id).first()
    if not ss:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    db.delete(ss)
    db.commit()
    return None
