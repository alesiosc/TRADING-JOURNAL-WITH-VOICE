from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import JournalEntry
from app.schemas import JournalEntryCreate, JournalEntryRead, JournalEntryUpdate
from app.services.websocket_manager import manager

router = APIRouter(prefix="/api/journal", tags=["journal"])


@router.get("/", response_model=List[JournalEntryRead])
def list_journal_entries(
    trade_id: int = Query(None, description="Filter by trade"),
    sentiment: str = Query(None, description="Filter by sentiment"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(JournalEntry)
    if trade_id is not None:
        query = query.filter(JournalEntry.trade_id == trade_id)
    if sentiment:
        query = query.filter(JournalEntry.sentiment == sentiment)
    return query.order_by(JournalEntry.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/{entry_id}", response_model=JournalEntryRead)
def get_journal_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return entry


@router.post("/", response_model=JournalEntryRead, status_code=201)
async def create_journal_entry(payload: JournalEntryCreate, db: Session = Depends(get_db)):
    entry = JournalEntry(**payload.model_dump())
    db.add(entry)
    db.commit()
    db.refresh(entry)
    await manager.broadcast({
        "type": "journal_created",
        "data": {
            "id": entry.id,
            "trade_id": entry.trade_id,
            "content": entry.content,
            "voice_transcript": entry.voice_transcript,
            "sentiment": entry.sentiment,
            "mood_before": entry.mood_before,
            "mood_after": entry.mood_after,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        },
    })
    return entry


@router.put("/{entry_id}", response_model=JournalEntryRead)
def update_journal_entry(entry_id: int, payload: JournalEntryUpdate, db: Session = Depends(get_db)):
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)
    db.commit()
    db.refresh(entry)
    return entry


@router.delete("/{entry_id}", status_code=204)
def delete_journal_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    db.delete(entry)
    db.commit()
    return None
