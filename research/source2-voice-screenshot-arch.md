# Source 2: Supplementary Analysis — Voice, Screenshotting & Architecture Deep Dive

## Voice Input Options (Free)

### Whisper.cpp
- **Best free option overall.** Runs locally, no API costs, extremely fast on modern CPUs (especially with ggml quantization). Supports real-time transcription via streaming.
- Setup: Clone repo, build with `make`, download a GGML model (small.en or base.en are fast enough). Pipe microphone input via `whisper-cli --stdin` or use language bindings (Python whisper-cpp, Node.js bindings).
- Accuracy: Near-perfect for clean audio. Handles trading jargon well if you provide a custom vocabulary list via `--prompt` parameter.
- Trade-specific: Can be set up to listen for hotkey-activated recording. Say "long ES 2 contracts at 5032.50" → Whisper transcribes → a parser extracts direction, instrument, size, price.

### Vosk
- Offline, smaller footprint than Whisper. Models are ~50MB vs Whisper's ~1GB.
- Good for embedded/low-power setups (Raspberry Pi, old laptop running journal).
- Accuracy lower than Whisper on noisy audio or niche vocabulary.

### Browser Speech Recognition API
- Built into Chrome/Edge via `webkitSpeechRecognition`. Zero setup.
- Free, unlimited, runs in the browser tab.
- Accuracy reasonable for English. Dies on heavy background noise.
- Best for quick "add trade: ..." voice commands in a web-based journal.

### Voice Command Patterns
- "Add trade long ES 2 contracts entry 5032.50 stop 5018 target 5060"
- "Tag last trade as breakout failure"
- "Show me my P&L for this week"
- "What's my win rate on Monday trades?"
- "Screenshot current chart" (triggers capture)

## Screenshot Capture & OCR

### Capture Methods (Free)
- **PIL/Pillow + mss** (Python): `mss.mss().shot()` — fastest cross-platform screen capture. Can capture specific monitor regions at 60fps.
- **DXGI** (Windows only): DirectX capture via `dxcam` Python library. Hardware-accelerated, 144fps capable. Perfect for capturing trading chart windows in real time.
- **Puppeteer/screenshot**: If trading platform is web-based, automated screenshots via headless browser.
- **AutoIt/AHK**: Windows automation for triggering captures on platform-native apps.

### OCR Options
- **Tesseract 5**: Free, local, well-established. Accuracy ~90% on clean screenshots. Needs preprocessing (grayscale, threshold, contrast enhancement) for best results. Use with pytesseract Python wrapper.
- **PaddleOCR**: Better accuracy than Tesseract (~95%), especially on mixed text/numbers. Heavier model. Good for extracting P&L numbers from trading platform screenshots.
- **Surya**: Newer, transformer-based OCR. Highest accuracy (~98%) but needs GPU. Overkill for simple number extraction.

## Recommended Architecture

### Database Schema (PostgreSQL)
```sql
trades(id, broker, account, instrument, direction, entry_price, exit_price,
       quantity, entry_time, exit_time, stop_loss, take_profit, tags, notes,
       screenshot_path, strategy, setup_type, market_session, emotion_entry,
       emotion_exit, created_at)

screenshots(id, trade_id, path, captured_at, ocr_text, platform)
tags(id, name, color)
trade_tags(trade_id, tag_id)
metrics_cached(id, metric_name, value, period_start, period_end, computed_at)
```

### Free Tier / Local AI Integration
- **Ollama**: Run Qwen3, DeepSeek-R1-distill, or Gemma3 locally. ~4-8GB RAM for 7B models.
- **Gemini API free tier**: 60 requests per minute free. Good for quick analyses without local GPU.
- **Grok free tier**: 10 requests per hour. Useful as fallback.
- **Strategy**: Primary = Ollama local (private, free, unlimited). Fallback = Gemini API (free tier). Emergency = Grok free.

### Real-Time Metrics Engine
- **DuckDB**: Best for analytics. In-process OLAP, query parquet/CSV directly, ~10x faster than SQLite for aggregations. Use for P&L calculations, rolling metrics, win rate by tag.
- **SQLite**: Best for transactional storage (trade entry, note saving). Use for the CRUD layer.
- **Polars**: Best for in-memory dataframes. Use for complex multi-dimensional analysis (clustering trades by setup + outcome + market condition).

### Sync Strategy (Free)
- **Syncthing**: P2P sync between devices. No cloud dependency. Journal DB syncs between desktop and laptop.
- **Local network share**: SMB/NFS for multi-computer setups.
- **SQLite WAL mode**: Allows reading DB while writing — journal can stay open on multiple devices.
