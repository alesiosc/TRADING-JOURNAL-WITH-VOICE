You are a senior trading technology analyst and full-stack developer. Do a deep research on building an all-purpose trading journal in mid-2026. The journal must be free (no paid subscriptions), self-hosted or local-first, and integrate AI features.

Cover every section below thoroughly with specific tools, APIs, libraries, and approaches.

## 1. Trade Data Capture — Manual & Automated

- Free trade import APIs/bridges for: Interactive Brokers, TD Ameritrade (if still alive), Tradovate, NinjaTrader, MetaTrader, cTrader, TradingView alerts
- Prop firm connections: FTMO, MFF, The Funded Trader — do they have APIs or export formats? Any free bridge tools?
- Manual entry UI options: what free frontend frameworks work for quick trade logging with hotkeys?
- Voice input: free/local speech-to-text options (Whisper, Vosk, Coqui STT) for saying "long ES 2 contracts at 5032.50, stop at 5018, target 5060" and auto-parsing into trade fields
- CSV/email import parsers for brokers without APIs

## 2. Real-Time Metrics & Analytics

- What free metrics engine? DuckDB vs SQLite vs Polars vs ClickHouse for trade data
- Real-time P&L, win rate, expectancy, Sharpe, Sortino, max drawdown — calculation approaches
- Rolling metrics (last 20 trades, today, this week, this month) without recomputing full history
- Session-based analytics (pre-market, regular, after-hours)
- Trade tags/categories filtering performance by setup type, market, time of day

## 3. Trade Screenshotting — Real-Time Capture

- Free screenshot methods: Python/PIL, Puppeteer/screenshot, Windows Magnification API, DirectX capture
- Auto-screenshot on trade entry/exit triggers
- OCR for extracting P&L, prices from broker/platform screenshots (Tesseract, PaddleOCR, Surya)
- Image organization and search (by date, ticker, setup pattern)
- Chart annotation overlay (mark entries/exits on screenshots)

## 4. AI Integrations — Free Tier / Local

- Running a local LLM (Qwen2.5, Gemma, Llama) via Ollama for trade journal analysis
- Free cloud AI APIs with generous free tiers (Google Gemini API free tier, Claude free, Grok free)
- Trade narrative generation — "review today's trades and highlight patterns"
- Sentiment analysis on trade journal notes
- Pattern recognition across tagged trades
- AI coach feature — analyzing losing streaks, suggesting adjustments

## 5. Multi-Broker / Multi-Account Aggregation

- Normalizing trade data from different brokers into a unified schema
- Handling different asset classes: futures, forex, stocks, crypto, options
- Performance comparison across accounts and brokers
- Risk exposure aggregation across all open positions

## 6. Architecture & Build Options

- Option A: Python desktop app (PyQt6/Tkinter/Flet) — simplest for local-first
- Option B: Web app (Next.js/Streamlit/Gradio) — best for cross-device access
- Option C: Obsidian vault with plugins (Dataview, Tracker) — leverages existing setup
- Database schema design for trades, screenshots, tags, notes
- Sync between devices (Syncthing, local network, or free tier of cloud)
- Mobile companion: Free app builder options for quick mobile trade logging

## 7. Existing Free Trading Journals & Projects

- List every free/open-source trading journal on GitHub — what features does each have?
- What gaps exist that a new project would need to fill?
- What's worth forking vs starting fresh?

## 8. Voice Input Deep Dive

- Whisper.cpp (local, fast, free) — setup complexity and accuracy
- Vosk — offline, smaller models
- Browser Speech Recognition API — free, built-in, limited
- Voice command patterns: "add trade [details]", "show me my P&L", "tag last trade as [tag]"
- Wake word / hands-free mode options

---

**Output format:** Provide the research as a structured markdown report with:
- Specific tool/library/API names with version info
- Links to GitHub repos, documentation, or articles
- Honest assessment of free tier limitations vs paid alternatives
- Build complexity rating for each component (easy / moderate / complex)
- Recommended architecture combining the best free options

**Edge cases to cover:**
- What happens when APIs change or get deprecated
- Rate limits on free AI APIs — mitigation strategies
- Data privacy concerns with cloud AI vs local models
- Backup and export strategies
