# Trading Journal With Voice

A free, local-first, AI-powered trading journal for futures, forex, stocks, crypto, and options traders.

**Zero subscriptions. Zero cloud lock-in. All your data stays on your machine.**

## Quick Start

```bash
# 1. Install dependencies
python setup.py --quick

# 2. Start everything
python start_journal.py

# 3. Open your browser
http://localhost:8000
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                     USER INTERFACE                   │
│  Frontend (React/Vite)       CLI (journal_cli.py)   │
└─────────────────────────┬───────────────────────────┘
                          │ HTTP / WebSocket
┌─────────────────────────▼───────────────────────────┐
│                   BACKEND (FastAPI)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Trades   │  │ Journal  │  │ Screenshots API  │   │
│  │ CRUD API │  │ Entries  │  │ (capture + serve)│   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ CSV      │  │ AI       │  │ Stats Engine    │   │
│  │ Import   │  │ (Ollama) │  │                  │   │
│  └──────────┘  └──────────┘  └──────────────────┘   │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│                   DATA LAYER                         │
│  ┌────────────────┐  ┌──────────────────────────┐   │
│  │ SQLite (CRUD)  │  │ DuckDB (Analytics)       │   │
│  │ trades.db      │  │ analytics.duckdb         │   │
│  └────────────────┘  └──────────────────────────┘   │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                 INPUT LAYER                          │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────┐  │
│  │ Voice Input  │ │ Screenshots  │ │ Brokers    │  │
│  │ Whisper.cpp  │ │ mss + OCR    │ │ API/CSV    │  │
│  └──────────────┘ └──────────────┘ └────────────┘  │
└─────────────────────────────────────────────────────┘
```

## Key Features

### 📊 Trade Journaling
- Manual trade entry via Web UI or CLI
- Auto-P&L calculation on close
- Scaling in/out via trade legs
- Tags, ratings, strategy tagging
- Screenshot attachments per trade
- Journal entries with mood tracking

### 🎤 Voice Input
- **Post-session dictation**: record voice memos, auto-transcribe with Whisper.cpp
- **Trade parsing**: "long ES 2 contracts at 5032.50" → structured trade data
- Hotkey-activated recording (Ctrl+Shift+V)
- Fully offline, no cloud services

### 📸 Screenshot Capture
- Global hotkey capture (Ctrl+Shift+S)
- Auto-capture on trade events (entry, exit, SL move)
- Region selection capture (Ctrl+Shift+R)
- Thumbnail generation
- Screenshot replay/flipbook viewer

### 🤖 AI Analysis (Local)
- **Trade Debrief**: AI coach reviews your trades (entry, exit, risk, psychology)
- **Auto-Tagging**: AI suggests behavioral tags based on trade patterns
- **Daily Summary**: AI-generated end-of-day recap
- All local via **Ollama** — no data leaves your machine

### 🔌 Multi-Broker Support
| Broker | Method | Status |
|--------|--------|--------|
| **Alpaca** | REST API | ✅ Ready |
| **IBKR** | ib_insync (TWS/Gateway) | ✅ Ready |
| **cTrader** | Open API (OAuth) | ✅ Ready |
| **Schwab** | Schwab API (post-TDA) | ✅ Ready |
| **TradingView** | Webhook → Flask endpoint | ⚙️ Configurable |
| **NT8 / MT4/5** | CSV Auto-Watcher | ✅ Ready |
| **Prop Firms** (FTMO/Apex/TFT) | CSV Import | ✅ Ready |
| **Any broker** | CSV Import + Column Mapper | ✅ Ready |

### 📈 Analytics
- Win rate, Profit Factor, Expectancy
- Sharpe/Sortino Ratio (via DuckDB)
- Equity curve generation
- Monthly/Strategy breakdown
- MFE/MAE analysis
- Rolling metrics (last N trades)

## Prerequisites

| Tool | Required? | For | Install |
|------|-----------|-----|---------|
| Python 3.10+ | ✅ Required | Everything | python.org |
| Node.js 18+ | ⚠️ Optional | Frontend UI | nodejs.org |
| Ollama | ⚠️ Optional | AI analysis | ollama.com |
| Whisper.cpp | ⚠️ Optional | Voice input | github.com/ggerganov/whisper.cpp |

## Configuration

All configuration is in `config/config.yaml`. Key settings:

```yaml
# Voice input
voice:
  enabled: true
  engine: whisper_cpp  # whisper_cpp | vosk | browser_api
  hotkey: ctrl+shift+v

# Screenshots
screenshots:
  capture_hotkey: ctrl+shift+s
  auto_capture: true

# AI
ai:
  enabled: true
  ollama:
    analysis_model: qwen3:8b  # or gemma3:4b for low-resource

# Brokers — enable and configure each
brokers:
  alpaca:
    enabled: true
    paper: true
  ibkr:
    enabled: false
```

API keys go in `.env` (never committed):
```
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
IBKR_PORT=7497
CTRADER_CLIENT_ID=your_client_id
```

## CLI Usage

```bash
# Start everything
python start_journal.py

# Or run components individually
python journal_cli.py server      # Backend only
python journal_cli.py ui          # Frontend only

# Manage trades
python journal_cli.py list        # List recent trades
python journal_cli.py open        # Show open trades
python journal_cli.py stats       # Show statistics

# Import data
python journal_cli.py import trades.csv
python journal_cli.py sync alpaca # Auto-fetch from Alpaca

# Voice
python journal_cli.py voice       # Record and transcribe

# AI
python journal_cli.py ai          # Daily summary
python journal_cli.py ai 42       # Analyze trade #42

# Export
python journal_cli.py export --format csv
```

## API Documentation

When the backend is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | /api/trades/ | List trades |
| POST | /api/trades/ | Create trade |
| GET | /api/trades/{id} | Get trade detail |
| PUT | /api/trades/{id} | Update trade |
| GET | /api/stats | Trading statistics |
| POST | /api/import/csv | Import CSV file |
| POST | /api/ai/debrief/{id} | AI trade analysis |
| POST | /api/ai/daily-summary | AI daily summary |
| POST | /api/screenshots/capture | Take screenshot |
| WS | /api/ws | Live trade updates |

## Database

Two databases work together:

| Database | Role | Location |
|----------|------|----------|
| **SQLite** | Trade CRUD, primary store | `trading_journal.db` |
| **DuckDB** | Analytics, fast aggregations | `analytics/analytics.duckdb` |

DuckDB auto-syncs from SQLite via the analytics engine.

## Voice Input Setup

### Option 1: Whisper.cpp (Recommended)
```bash
git clone https://github.com/ggerganov/whisper.cpp
cd whisper.cpp
cmake -B build
cmake --build build --config Release
bash models/download-ggml-model.sh tiny
# Add whisper-cli to your PATH
```

### Option 2: Vosk (Lightweight)
```bash
# Download a model from https://alphacephei.com/vosk/models
# Set vosk.model_path in config.yaml
```

## AI Setup

```bash
# Install Ollama
# https://ollama.com/download

# Pull models
ollama pull qwen3:8b        # General analysis
ollama pull nomic-embed-text  # For similarity search

# Optional: vision model for screenshot analysis
ollama pull llava:7b
```

## Existing Data Preserved

The following are NOT deleted or modified:
- `trading_journal.db` — Your trade database
- `research/` — TradeViz and all research files
- `prompts/` — Kimi deep research results
- `trading_notes/` — Existing voice/note transcriptions
- `screenshots/` — Existing screenshot captures
- `backend/` — Existing FastAPI backend
- `frontend/` — Existing React frontend
- `screenshot_module/` — Screenshot capture module
- `stt_module/` — Speech-to-text module
- `broker_watcher/` — CSV auto-watcher

## Project Structure

```
Trading Journal With Voice/
├── start_journal.py           # Master launcher
├── journal_cli.py             # CLI interface
├── setup.py                   # Setup/install script
├── config/
│   └── config.yaml            # Master configuration
├── backend/                   # FastAPI backend
│   ├── app/
│   │   ├── main.py            # FastAPI app
│   │   ├── models.py          # SQLAlchemy models
│   │   ├── schemas.py         # Pydantic schemas
│   │   ├── database.py        # DB connection
│   │   ├── routers/           # API endpoints
│   │   └── services/          # Business logic
│   └── run.py
├── frontend/                  # React frontend
│   ├── src/                   # Source code
│   └── dist/                  # Built files
├── brokers/                   # Broker connectors
│   ├── __init__.py            # Base connector interface
│   ├── alpaca_connector.py    # Alpaca API
│   ├── ibkr_connector.py      # Interactive Brokers
│   ├── ctrader_connector.py   # cTrader
│   ├── schwab_connector.py    # Charles Schwab
│   └── csv_normalizer.py      # CSV import for all brokers
├── voice/                     # Voice input module
│   └── __init__.py            # Whisper.cpp + Vosk
├── analytics/                 # Analytics engine
│   └── __init__.py            # DuckDB metrics
├── broker_watcher/            # CSV auto-watcher
├── screenshot_module/         # Screenshot capture
├── stt_module/                # Speech-to-text module
├── prompts/                   # Research documents
├── research/                  # Existing research files
├── screenshots/               # Captured screenshots
├── voice_recordings/          # Recorded audio
├── exports/                   # Export output
└── logs/                      # Application logs
```

## License

Free for personal and non-commercial use.
Built with ❤️ for traders who value privacy and independence.
