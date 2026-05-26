from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    Text,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Instrument
# ---------------------------------------------------------------------------
class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=True)
    asset_class = Column(String(50), nullable=False, default="futures")  # futures, stock, forex, crypto, index
    point_value = Column(Float, default=1.0)
    tick_size = Column(Float, default=0.01)
    exchange = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    trades = relationship("Trade", back_populates="instrument")


# ---------------------------------------------------------------------------
# Trade
# ---------------------------------------------------------------------------
class Trade(Base):
    __tablename__ = "trades"

    id = Column(Integer, primary_key=True, index=True)
    instrument_id = Column(Integer, ForeignKey("instruments.id"), nullable=False, index=True)

    # Core trade fields
    symbol = Column(String(50), nullable=True, index=True)  # denormalized for quick access
    direction = Column(String(10), nullable=False)  # long / short
    quantity = Column(Float, nullable=True)  # renamed from volume for clarity
    volume = Column(Float, nullable=False)  # kept for backwards compatibility

    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)

    entry_time = Column(DateTime, nullable=False, default=utcnow)
    exit_time = Column(DateTime, nullable=True)

    # PnL & costs
    pnl = Column(Float, nullable=True)
    pnl_pct = Column(Float, nullable=True)
    fees = Column(Float, default=0.0)  # renamed from commission for clarity
    commission = Column(Float, default=0.0)  # kept for backwards compatibility

    # Metadata
    status = Column(String(10), nullable=False, default="open")  # open / closed
    setup_type = Column(String(100), nullable=True)  # e.g. breakout, pullback, reversal
    strategy = Column(String(200), nullable=True)  # renamed from strategy_tag
    strategy_tag = Column(String(200), nullable=True)  # kept for backwards compatibility
    broker = Column(String(50), nullable=True)
    account_id = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    rating = Column(Integer, nullable=True)  # 1-5

    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    # relationships
    instrument = relationship("Instrument", back_populates="trades")
    legs = relationship("TradeLeg", back_populates="trade", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="trade", cascade="all, delete-orphan")
    screenshots = relationship("Screenshot", back_populates="trade", cascade="all, delete-orphan")
    tags = relationship("Tag", secondary="trade_tags", back_populates="trades")


# ---------------------------------------------------------------------------
# TradeLeg  (scaling in/out)
# ---------------------------------------------------------------------------
class TradeLeg(Base):
    __tablename__ = "trade_legs"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=False, index=True)
    type = Column(String(20), nullable=False)  # entry / exit / add / reduce
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)  # renamed from volume
    volume = Column(Float, nullable=False)  # kept for backwards compatibility
    timestamp = Column(DateTime, default=utcnow)  # renamed from time
    time = Column(DateTime, default=utcnow)  # kept for backwards compatibility

    trade = relationship("Trade", back_populates="legs")


# ---------------------------------------------------------------------------
# JournalEntry
# ---------------------------------------------------------------------------
class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True, index=True)
    content = Column(Text, nullable=False)
    mood = Column(String(50), nullable=True)  # simplified mood field
    voice_transcript = Column(Text, nullable=True)
    sentiment = Column(String(30), nullable=True)  # positive/negative/neutral/anxious/confident
    mood_before = Column(String(50), nullable=True)
    mood_after = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    trade = relationship("Trade", back_populates="journal_entries")


# ---------------------------------------------------------------------------
# Screenshot
# ---------------------------------------------------------------------------
class Screenshot(Base):
    __tablename__ = "screenshots"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True, index=True)
    type = Column(String(30), nullable=False, default="manual")  # entry/mid/exit/modification/manual
    filepath = Column(String(500), nullable=False)  # renamed from file_path
    file_path = Column(String(500), nullable=False)  # kept for backwards compatibility
    thumbnail_path = Column(String(500), nullable=True)
    trigger_event = Column(String(50), nullable=True)
    auto_captured = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)  # renamed from captured_at
    captured_at = Column(DateTime, default=utcnow)  # kept for backwards compatibility

    trade = relationship("Trade", back_populates="screenshots")


# ---------------------------------------------------------------------------
# Tag
# ---------------------------------------------------------------------------
class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    color = Column(String(7), nullable=True)  # hex e.g. "#ff6b6b"
    created_at = Column(DateTime, default=utcnow)

    trades = relationship("Trade", secondary="trade_tags", back_populates="tags")


# ---------------------------------------------------------------------------
# TradeTag  (association)
# ---------------------------------------------------------------------------
class TradeTag(Base):
    __tablename__ = "trade_tags"

    trade_id = Column(Integer, ForeignKey("trades.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)
