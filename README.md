# Trading Journal — Stripped Core

A free, local-first trading journal. Stripped-down v1 with just the essentials.

## Quick Start

```bash
# 1. Install backend deps
pip install -r backend/requirements.txt

# 2. Install frontend deps
cd frontend && npm install && cd ..

# 3. Start everything
python start_journal.py
```

Open http://localhost:5173 in your browser.

## What's Included

### Backend (FastAPI)
- **Trades CRUD** — Create, list, edit, close trades with auto P&L
- **Journal Entries** — Notes, mood tracking, sentiment per trade
- **Instruments** — Symbol database (ES, NQ, CL, etc.)
- **Tags** — Label trades (breakout, pullback, reversal)
- **Screenshots** — Upload, view, lightbox, flipbook replay
- **CSV Import** — Upload trade CSV files with column mapping
- **Stats** — Win rate, profit factor, equity curve, monthly breakdown

### Frontend (React)
- **Dashboard** — Stats cards, equity curve, monthly P&L chart
- **Trades** — Filterable, sortable trade list
- **Trade Detail** — Full view with journal entries, screenshot gallery
- **CSV Import** — Drag-and-drop with column mapper

## What's Stripped Out (Add Back Later)

- Broker sync (Alpaca, IBKR, cTrader, Schwab)
- AI trade debrief (Ollama)
- Vision analysis (chart screenshot AI)
- Prop firm rule tracking (FTMO/TopStep)
- Active trade tracker
- Advanced analytics (DuckDB)
- Voice input (Whisper/Vosk)
- CSV auto-watcher
- WebSocket live updates
- Brokers page / Daily Summary page

## Configuration

Edit `config/config.yaml`:
```yaml
backend:
  port: 8000
screenshots:
  capture_hotkey: ctrl+shift+s
  auto_capture: true
```

## Run

| Command | What It Does |
|---------|-------------|
| `python start_journal.py` | Backend + Frontend |
| `python start_journal.py --no-ui` | Backend only |
| `python start_journal.py --port 8080` | Custom port |

## API

- **Swagger UI**: http://localhost:8000/docs
- **Health**: http://localhost:8000/api/health

Built with Python, FastAPI, SQLite, React, and Vite.
