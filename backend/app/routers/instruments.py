from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Instrument
from app.schemas import InstrumentCreate, InstrumentRead

router = APIRouter(prefix="/api/instruments", tags=["instruments"])


@router.get("/", response_model=List[InstrumentRead])
def list_instruments(
    search: str = Query(None, description="Filter by symbol (case-insensitive)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    query = db.query(Instrument)
    if search:
        query = query.filter(Instrument.symbol.ilike(f"%{search}%"))
    return query.order_by(Instrument.symbol).offset(skip).limit(limit).all()


@router.post("/", response_model=InstrumentRead, status_code=201)
def create_instrument(payload: InstrumentCreate, db: Session = Depends(get_db)):
    # Check for duplicate symbol
    existing = db.query(Instrument).filter(Instrument.symbol == payload.symbol).first()
    if existing:
        raise HTTPException(status_code=409, detail=f"Instrument '{payload.symbol}' already exists")
    instr = Instrument(**payload.model_dump())
    db.add(instr)
    db.commit()
    db.refresh(instr)
    return instr


@router.get("/{instrument_id}", response_model=InstrumentRead)
def get_instrument(instrument_id: int, db: Session = Depends(get_db)):
    instr = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instr:
        raise HTTPException(status_code=404, detail="Instrument not found")
    return instr


@router.get("/by-symbol/{symbol}", response_model=InstrumentRead)
def get_instrument_by_symbol(symbol: str, db: Session = Depends(get_db)):
    instr = db.query(Instrument).filter(Instrument.symbol.ilike(symbol)).first()
    if not instr:
        raise HTTPException(status_code=404, detail=f"Instrument '{symbol}' not found")
    return instr
