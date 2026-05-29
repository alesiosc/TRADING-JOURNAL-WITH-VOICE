"""Seed the database with sample trades so the dashboard has data to show."""
import sys, os, random
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))
os.chdir(os.path.join(os.path.dirname(__file__), "backend"))

from app.database import SessionLocal, engine, Base
from app.models import Instrument, Trade, TradeLeg, JournalEntry, Tag, TradeTag

# Create tables
Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Check if already seeded
existing = db.query(Trade).count()
if existing > 5:
    print(f"Database already has {existing} trades — skipping seed")
    db.close()
    sys.exit(0)

# Clear existing instruments if any (clean seed)
db.query(Instrument).delete()
db.commit()

# Instruments
instruments = {
    "ES": Instrument(symbol="ES", name="S&P 500 E-mini Futures", asset_class="futures", point_value=50.0, tick_size=0.25),
    "NQ": Instrument(symbol="NQ", name="Nasdaq-100 E-mini Futures", asset_class="futures", point_value=20.0, tick_size=0.25),
    "CL": Instrument(symbol="CL", name="Crude Oil Futures", asset_class="futures", point_value=1000.0, tick_size=0.01),
    "GC": Instrument(symbol="GC", name="Gold Futures", asset_class="futures", point_value=100.0, tick_size=0.10),
    "EURUSD": Instrument(symbol="EURUSD", name="Euro / US Dollar", asset_class="forex", point_value=1.0, tick_size=0.0001),
}
for instr in instruments.values():
    db.add(instr)
db.commit()

# Tags
tags = ["breakout", "pullback", "reversal", "momentum", "FVG", "liquidity-grab", "range"]
tag_objs = {}
for t in tags:
    obj = Tag(name=t)
    db.add(obj)
    db.commit()
    tag_objs[t] = obj

# Sample trades
now = datetime.now(timezone.utc)
sample_trades = [
    # (instrument_symbol, direction, volume, entry, exit, sl, tp, minutes_open, pnl, setup, notes)
    ("ES", "long", 2, 5245.50, 5278.25, 5238.00, 5300.00, 45, 3275.00, "breakout", "Clean breakout above resistance. Volume confirmed."),
    ("NQ", "short", 1, 18420.00, 18355.50, 18450.00, 18300.00, 30, 1290.00, "reversal", "Rejected at prior day high. Good risk/reward."),
    ("ES", "short", 3, 5260.00, 5275.50, 5240.00, None, 20, -2325.00, "breakout", "Fake breakout. Stopped out at prior high."),
    ("CL", "long", 1, 78.45, 79.82, 78.00, 80.50, 60, 1370.00, "momentum", "Strong bid all session. Held through pullback."),
    ("NQ", "long", 2, 18480.00, 18420.00, 18460.00, None, 15, -1200.00, "pullback", "Entered too early. Failed to hold level."),
    ("GC", "short", 1, 2340.20, 2318.60, 2346.00, 2320.00, 90, 2160.00, "reversal", "Double top at resistance. Perfect short setup."),
    ("ES", "long", 2, 5255.00, 5248.50, 5251.00, 5270.00, 10, -650.00, "FVG", "Fair value gap filled then continued lower. Bad entry."),
    ("EURUSD", "long", 50000, 1.0820, 1.0855, 1.0800, 1.0880, 120, 175.00, "pullback", "Pullback to trendline. Held for full move."),
    ("ES", "short", 1, 5272.00, 5248.00, 5280.00, 5240.00, 55, 1200.00, "breakout", "Failed breakout of range. Rested below VWAP."),
    ("NQ", "long", 3, 18390.00, 18410.00, 18380.00, 18420.00, 8, 600.00, "momentum", "Scalped quick bounce at support."),
    ("ES", "short", 2, 5240.00, 5242.50, 5245.00, None, 5, -250.00, "liquidity-grab", "Premature short. Liquidity grab took me out."),
    ("CL", "short", 1, 79.50, 78.10, 79.80, 77.80, 75, 1400.00, "range", "Trading range top. Short to bottom of range."),
]

base_time = now - timedelta(days=14)
for i, (sym, direction, vol, entry, exit, sl, tp, mins, pnl, setup, notes) in enumerate(sample_trades):
    instr = db.query(Instrument).filter(Instrument.symbol == sym).first()
    entry_time = base_time + timedelta(days=i, hours=random.randint(8, 16), minutes=random.randint(0, 59))
    exit_time = entry_time + timedelta(minutes=mins)

    # Point value by instrument
    pv = instr.point_value if instr else 1.0
    pnl_pct = round((pnl / (entry * vol * pv)) * 100, 2) if entry > 0 else 0

    trade = Trade(
        instrument_id=instr.id,
        symbol=sym,
        direction=direction,
        quantity=vol,
        volume=vol,
        entry_price=entry,
        exit_price=exit,
        stop_loss=sl,
        take_profit=tp,
        entry_time=entry_time,
        exit_time=exit_time,
        pnl=pnl,
        pnl_pct=pnl_pct,
        fees=random.uniform(2, 8),
        commission=random.uniform(2, 8),
        status="closed",
        setup_type=setup,
        strategy_tag=setup,
        broker="manual",
        account_id="main",
        notes=notes,
        rating=random.randint(3, 5),
    )
    db.add(trade)
    db.commit()

    # Add a leg
    leg = TradeLeg(
        trade_id=trade.id,
        type="entry",
        price=entry,
        quantity=vol,
        volume=vol,
        timestamp=entry_time,
        time=entry_time,
    )
    db.add(leg)

    # Add journal entry
    moods = [
        "Focused, saw the setup clearly",
        "Nervous but followed the plan",
        "Felt rushed, should have waited",
        "Calm and patient, waited for confirmation",
        "Overconfident, took a low-probability setup",
    ]
    sentiments = ["confident", "anxious", "neutral", "confident", "negative"]
    journal = JournalEntry(
        trade_id=trade.id,
        content=random.choice(moods),
        mood_before=random.choice(["Focused", "Nervous", "Calm", "Excited"]),
        mood_after=random.choice(["Satisfied", "Regretful", "Neutral", "Relieved"]),
        sentiment=random.choice(sentiments),
        created_at=exit_time + timedelta(minutes=random.randint(5, 60)),
    )
    db.add(journal)

    # Add random tags
    trade_tags = random.sample(tags, random.randint(1, 3))
    for t in trade_tags:
        db.execute(TradeTag.__table__.insert().values(trade_id=trade.id, tag_id=tag_objs[t].id))

db.commit()
db.close()

print(f"Seeded {len(sample_trades)} sample trades with legs, journal entries, and tags")
