from __future__ import annotations
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ===========================================================================
# Instrument
# ===========================================================================
class InstrumentBase(BaseModel):
    symbol: str
    name: Optional[str] = None
    asset_class: str = "futures"
    point_value: float = 1.0
    tick_size: float = 0.01
    exchange: Optional[str] = None


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentUpdate(BaseModel):
    symbol: Optional[str] = None
    name: Optional[str] = None
    asset_class: Optional[str] = None
    point_value: Optional[float] = None
    tick_size: Optional[float] = None
    exchange: Optional[str] = None


class InstrumentRead(InstrumentBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# TradeLeg
# ===========================================================================
class TradeLegBase(BaseModel):
    type: str  # entry / exit / add / reduce
    price: float
    quantity: float = Field(default=1.0, alias="volume")
    volume: float = 1.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    time: Optional[datetime] = None


class TradeLegCreate(TradeLegBase):
    pass


class TradeLegRead(TradeLegBase):
    id: int
    trade_id: int

    model_config = {"from_attributes": True}


# ===========================================================================
# Trade
# ===========================================================================
class TradeBase(BaseModel):
    instrument_id: int
    symbol: Optional[str] = None
    direction: str  # long / short
    quantity: Optional[float] = None
    volume: float = 1.0
    entry_price: float
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    entry_time: datetime = Field(default_factory=datetime.utcnow)
    exit_time: Optional[datetime] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    fees: float = 0.0
    commission: float = 0.0
    status: str = Field(default="open")
    setup_type: Optional[str] = None
    strategy: Optional[str] = None
    strategy_tag: Optional[str] = None
    broker: Optional[str] = None
    account_id: Optional[str] = None
    notes: Optional[str] = None
    rating: Optional[int] = None


class TradeCreate(TradeBase):
    legs: Optional[List[TradeLegCreate]] = None
    tags: Optional[List[str]] = None  # tag names


class TradeUpdate(BaseModel):
    instrument_id: Optional[int] = None
    symbol: Optional[str] = None
    direction: Optional[str] = None
    quantity: Optional[float] = None
    volume: Optional[float] = None
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    entry_time: Optional[datetime] = None
    exit_time: Optional[datetime] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None
    fees: Optional[float] = None
    commission: Optional[float] = None
    status: Optional[str] = None
    setup_type: Optional[str] = None
    strategy: Optional[str] = None
    strategy_tag: Optional[str] = None
    broker: Optional[str] = None
    account_id: Optional[str] = None
    notes: Optional[str] = None
    rating: Optional[int] = None
    tags: Optional[List[str]] = None


class TradeRead(TradeBase):
    id: int
    created_at: datetime
    updated_at: datetime
    instrument: Optional[InstrumentRead] = None
    legs: Optional[List[TradeLegRead]] = None
    journal_entries: Optional[List[JournalEntryRead]] = None
    screenshots: Optional[List[ScreenshotRead]] = None
    tags: Optional[List[TagRead]] = None

    model_config = {"from_attributes": True}


# ===========================================================================
# JournalEntry
# ===========================================================================
class JournalEntryBase(BaseModel):
    trade_id: Optional[int] = None
    content: str
    mood: Optional[str] = None
    voice_transcript: Optional[str] = None
    sentiment: Optional[str] = None
    mood_before: Optional[str] = None
    mood_after: Optional[str] = None


class JournalEntryCreate(JournalEntryBase):
    pass


class JournalEntryUpdate(BaseModel):
    content: Optional[str] = None
    mood: Optional[str] = None
    voice_transcript: Optional[str] = None
    sentiment: Optional[str] = None
    mood_before: Optional[str] = None
    mood_after: Optional[str] = None


class JournalEntryRead(JournalEntryBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# Screenshot
# ===========================================================================
class ScreenshotBase(BaseModel):
    trade_id: Optional[int] = None
    type: str = "manual"
    filepath: str = Field(default="", alias="file_path")
    file_path: str = ""
    thumbnail_path: Optional[str] = None
    trigger_event: Optional[str] = None
    auto_captured: bool = False


class ScreenshotCreate(ScreenshotBase):
    pass


class ScreenshotUpdate(BaseModel):
    trade_id: Optional[int] = None
    type: Optional[str] = None
    filepath: Optional[str] = None
    file_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    trigger_event: Optional[str] = None
    auto_captured: Optional[bool] = None


class ScreenshotRead(ScreenshotBase):
    id: int
    created_at: datetime
    captured_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ===========================================================================
# Tag
# ===========================================================================
class TagBase(BaseModel):
    name: str
    color: Optional[str] = None


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None


class TagRead(TagBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ===========================================================================
# TradeTag (association)
# ===========================================================================
class TradeTagCreate(BaseModel):
    trade_id: int
    tag_id: int


class TradeTagRead(TradeTagCreate):
    model_config = {"from_attributes": True}


# ===========================================================================
# Analytics
# ===========================================================================
class AnalyticsSummary(BaseModel):
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    avg_pnl: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    expectancy: float = 0.0
    avg_r_multiple: float = 0.0


class EquityCurvePoint(BaseModel):
    date: str
    cumulative_pnl: float
    daily_pnl: Optional[float] = None


class MFEPoint(BaseModel):
    trade_id: int
    mfe: float  # maximum favorable excursion (%)
    mae: float  # maximum adverse excursion (%)
    pnl: float


class RollingWindow(BaseModel):
    window: int
    win_rate: float
    avg_pnl: float
    profit_factor: float


# ===========================================================================
# Health check
# ===========================================================================
class HealthResponse(BaseModel):
    status: str
