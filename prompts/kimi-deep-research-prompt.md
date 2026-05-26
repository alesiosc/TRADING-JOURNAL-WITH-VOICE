# Kimi Deep Research Prompt — Free All-Purpose Trading Journal (Mid 2026)

Run this through Kimi's Deep Research mode. It combines 3 research sources
and asks Kimi to produce a comparison table, decision matrix, and ranked stacks.

---

I'm building a FREE all-purpose trading journal in mid-2026. Self-hosted, local-first, with AI. I have 3 research sources. Analyze them all, add your own research, and produce: (1) comparison table of ALL free trading journal tools, (2) decision matrix to pick components by trader type, (3) your own additions/corrections, (4) top 3 recommended stacks.

SOURCE 1 (ChatGPT):
Best open-source platforms are TradeNote (lightweight journal), TradeTally (best modern Docker-based with Schwab/IBKR/Tradovate sync and AI insights), OpenTradex (AI cockpit for developers), OpenBB (analytics backbone). Recommended stack: TradeTally UI + PostgreSQL+DuckDB + Ollama+Qwen3 + Obsidian + n8n + Docker Compose. Three build paths: non-dev (TradeTally+Docker+Ollama), power user (TradeNote+PostgreSQL+OpenBB+n8n), quant (OpenTradex+LangGraph+custom UI).

SOURCE 2 (Voice, Screenshots, Architecture):
Voice input via Whisper.cpp (best free/local), Vosk (lighter), Browser Speech API (zero-setup). Screenshots via mss+dxcam (Python, free, 144fps) with OCR via Tesseract 5/PaddleOCR/Surya. Database: DuckDB for analytics, SQLite for CRUD, Polars for complex analysis. Sync via Syncthing (P2P free). Full PostgreSQL schema provided.

SOURCE 3 (Broker APIs, Prop Firms, Aggregation):
Free broker APIs — IBKR (ib_insync, best), Tradovate (paid API access), cTrader (best free forex API), Schwab API (free), Alpaca (free crypto/stocks), TradingView webhooks. Prop firms (FTMO, TFT, MFF) have NO APIs — only CSV export via headless browser. Full unified trade schema for multi-broker normalization. Cost comparison table for every component.

OUTPUT: Comparison table, decision matrix, your own analysis of what's missing, and ranked stacks.
