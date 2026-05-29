# Where Am I Upto

## Last Updated: 2026-05-29

---

## Project Status: STRIPPED CORE v1

Stripped the full v2 build down to just the essentials. Everything else is
available as add-on modules to plug in later.

### Kept (Core)
- Trades CRUD + P&L
- Journal Entries (mood, sentiment, voice notes)
- Instruments / Tags
- Screenshots (upload, lightbox, flipbook)
- CSV Import (column mapper)
- Stats (win rate, equity curve, monthly)
- Dashboard / Trades / TradeDetail / Import UI

### Removed (Available to Add Back)
- Broker Sync (Alpaca, IBKR, cTrader, Schwab)
- AI Trade Debrief (Ollama)
- Vision Analysis (Ollama vision)
- Prop Firm Rules (FTMO/TopStep)
- Active Trade Tracker
- Advanced Analytics (DuckDB)
- Voice Input (Whisper/Vosk/Zavi + STT module)
- CSV Auto-Watcher
- WebSocket
- Brokers page / Daily Summary page
- Voice Trade Button

### To start: python start_journal.py
### API docs: http://localhost:8000/docs
