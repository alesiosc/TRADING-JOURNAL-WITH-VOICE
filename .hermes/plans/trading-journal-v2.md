# Trading Journal V2 — Full Rebuild Plan

## Vision
A real-time, multi-broker trading journal with auto chart screenshots, intuitive UI, voice/AI operation, and deep statistics. Desktop-first web app, Python backend.

---

## Tech Stack

| Layer | Choice | Why |
|-------|--------|-----|
| Backend | Python FastAPI | Async, WebSocket-native, great for real-time trade feeds |
| Database | PostgreSQL | Best for analytics queries (win rate, sharpe over date ranges). SQLite fallback for single-user |
| Frontend | React + Tailwind + Recharts | Fast, modern, charting built-in |
| Real-time | WebSocket | Live trade updates from brokers → UI |
| Voice STT | Whisper (local via faster-whisper) | Already in project, free, works offline |
| Voice TTS | Edge TTS | Free, Windows-native |
| Screenshots | `mss` + OpenCV | Fast screen capture, chart area detection |
| Auth | API key / local-only | Single-user or trusted LAN |
| Hosting | Localhost + optional tailscale | Keep trading data local |

---

## Phases

### Phase 1 — Core Engine + Journal UI (build this first)
*Goal: working journal with manual entry, trade log, basic stats*

- **FastAPI backend** with WebSocket support
- **Database schema**: instruments, trades, trade_legs, journal_entries, screenshots, tags
- **REST API**: CRUD for trades, journals, screenshots
- **React frontend**:
  - Dashboard — today's P&L, open positions, recent trades
  - Trade log — filterable/sortable list with inline edit
  - Trade detail view — entry/exit info, journal notes, screenshots
  - Journal entry form — rich text, tags, emotions, voice notes
- **Statistics engine**: win rate, profit factor, avg win/loss, max drawdown, expectancy, Sharpe ratio, monthly P&L
- **Reuse from existing project**: STT module (`stt_gui.py`), voice-to-text pipeline

### Phase 2 — Screenshot System
*Goal: auto + manual chart capture, organized per trade*

- **Hotkey-based capture** (global hotkey → mss screenshot)
- **Auto-capture triggers**: on trade entry, at configurable interval mid-trade, on exit
- **Smart crop**: detect chart area via OpenCV (or simple region config)
- **Storage**: local filesystem by date/trade, thumbnails generated
- **UI**: screenshot gallery per trade, click-to-expand, delete/replace
- **Optional**: Cloudinary upload (already have code for this)

### Phase 3 — Broker Connectors (Plugin Architecture)
*Goal: real-time trade data from actual brokers*

- **Plugin interface**: each broker implements `get_positions()`, `get_orders()`, `on_trade()`, `on_price()`
- **Base connector class** with retry, auth, reconnection logic
- **Connectors to build** (priority order):
  1. **MT4/MT5** — MQL bridge (socket or file export). This covers FTMO, Top Step, and most prop firms
  2. **NinjaTrader 8** — NT8 C# API or file-based export (TradePerformance CSV)
  3. **Quantower** — Quantower API / file export
  4. **Rithmic / Edge Clear / AMP** — Rithmic REST API (CQG/CQG Continuum)
- **Fallback**: manual entry always works, auto-detect when no broker connected

### Phase 4 — Voice & AI Features
*Goal: operate the journal hands-free, get AI-powered trade analysis*

- **Voice journal entry**: press hotkey → speak notes → Whisper transcribes → AI structures into journal entry → saved
- **Voice commands**: "Show me today's P&L", "What's my win rate this month?", "Open last NQ trade"
- **AI trade review**: after trade closes, AI analyzes entry/exit, screenshots, journal → generates debrief
- **Pattern detection**: AI identifies recurring mistakes, strengths, patterns in your trading

### Phase 5 — Statistics Dashboard & Polish
*Goal: beautiful, insightful stats*

- **Charts**: equity curve, P&L distribution, monthly bar chart, drawdown chart
- **Reports**: weekly/monthly summaries with key metrics
- **Export**: CSV, PDF report
- **Filtering**: by date range, instrument, strategy tag, direction
- **Session notes**: daily trading session recap with AI summary

---

## Database Schema (Core Tables)

```
instruments: id, symbol, name, asset_class, exchange
trades: id, instrument_id, direction, volume, entry_price, exit_price,
        entry_time, exit_time, pnl, pnl_pct, status (open/closed),
        broker, strategy_tag, screenshot_count
journal_entries: id, trade_id, content, voice_transcript, sentiment,
                 tags[], created_at, updated_at
screenshots: id, trade_id, type (entry/mid/exit/manual), file_path,
             thumbnail_path, timestamp, auto_captured
sessions: id, date, notes, total_pnl, trade_count, win_count
stats_cache: id, period (day/week/month), json_data, updated_at
```

---

## Architecture Diagram

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  MT4/MT5     │    │  NinjaTrader │    │  Quantower   │
│  (MQL sock)  │    │  (NT8 API)   │    │  (C# API)    │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                    ┌──────▼───────┐
                    │   FastAPI    │◄──── WebSocket ────► React UI
                    │   Backend    │◄──── REST API
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
              ▼            ▼            ▼
         PostgreSQL    Screenshots    Whisper STT
         (trades,      (filesystem)   (voice input)
          stats)
```

---

## Key Design Decisions

1. **Plugin broker architecture** — new broker = one file implementing the interface. Start with MT4/MT5 since it covers most prop firms
2. **Screenshot-first** — capture is cheap, store aggressively, let UI sort/display. Auto-capture on trade events via hotkey simulation or broker callbacks
3. **Voice is primary input** — journal entries should be faster to speak than type. Whisper for transcription, local for privacy
4. **Stats cached** — compute on trade close, cache per period, invalidate on data change. Avoids slow queries on dashboard
5. **Single-binary distribution** — FastAPI backend packaged with PyInstaller or similar for easy deployment

---

## Non-Goals (V1)

- Mobile app (web responsive is enough)
- Social/sharing features
- Advanced backtesting integration
- Real-time market data feed (prices come from broker trade data)
- Multi-user/collaboration

---

## My Additions / Suggestions

1. **Tag-based strategy tracking** — tag each trade with strategy (supply/demand, momentum, scalping, etc.) so stats filterable by approach
2. **Trading session concept** — group trades by date/session, add pre-session plan and post-session review
3. **Trade rating** — rate each trade 1-5 after close, track if you followed your rules. Huge for accountability
4. **Auto-tagging** — AI suggests tags based on entry/exit behavior (e.g. "early exit", "fomo entry", "good risk management")
5. **Weekly digest** — auto-generated report sent via email or Telegram with key metrics and AI observations
6. **One-click replay** — click a closed trade to see entry chart → mid screenshots → exit chart in sequence, like a flipbook
