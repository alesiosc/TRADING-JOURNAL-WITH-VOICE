# Kimi Deep Research Result — Free Trading Journal (Mid 2026)

Source: Kimi Deep Research (run May 2026)
Full output below. Use this to restart the Trading Journal With Voice project from scratch.

---

Free Self-Hosted Trading Journal: Deep Research Report (Mid-2026)

Source Legend
- S1 = ChatGPT source recommendations  
- S2 = Voice/Screenshots/Architecture source  
- S3 = Broker APIs/Prop Firms/Aggregation source  
- NEW = Independent research additions/corrections  

---

1. MASTER COMPARISON TABLE: ALL Free Trading Journal Tools

Tool	License	Self-Host	DB	Broker Sync	AI	Mobile	Best For	5-Year TCO	
TradeNote	GPL-3.0	✅ Docker	MongoDB	20+ CSV templates	❌ Native	✅ Responsive	Privacy-first devs	0 + time	
TradeTally	Open Source	✅ Docker	PostgreSQL	7 brokers (Schwab/IBKR/ToS/etc)	✅ Google Gemini	✅ iOS app	Non-dev power users	0 + time	
OpenTradex	Open Source	✅ npm/CLI	Local JSON/SQLite	12 connectors (Alpaca/IBKR/Binance/etc)	✅ BYO Model (Ollama/OpenAI/Anthropic)	✅ Electron/iOS	Multi-asset cockpit builders	0 + time	
Deltalytix	CC BY-NC 4.0	⚠️ Docker coming	PostgreSQL (Supabase)	Tradovate/Rithmic/IBKR/FTMO	✅ AI agents + Coach	⚠️ In dev	Prop firm / futures traders	0 non-commercial	
OpenBB Terminal	AGPL-3.0	✅ Python/Docker	Local/Arrow	Import via CSV/API	✅ Quant/ML analytics	❌ CLI only	Research & analytics backbone	0	
Ghostfolio	AGPL-3.0	✅ Docker	PostgreSQL	Manual CSV	❌	✅ Web	Portfolio tracking (EU/FIRE)	0	
Myfxbook	Proprietary	❌ Cloud	N/A	MT4/MT5 auto-sync	❌	✅ Web/app	Forex traders only	0	
TradesViz	Freemium	❌ Cloud	N/A	200+ CSV imports	⚠️ Basic	✅ Web	High-volume free tier (3K/mo)	0–720	
TraderVue	Freemium	❌ Cloud	N/A	80+ CSV imports	❌	✅ Web	Part-time traders (100/mo)	0–1,740	
Stonk Journal	Free tier	❌ Cloud	N/A	Limited	❌	✅ Web	Community/sharing focus	0	
JournalPlus	Proprietary	❌ Cloud	N/A	200+ brokers	✅ AI chat	✅ Web	One-time 159 vs subscription	159	
Excel/Sheets	Commercial	✅ Local	File	Manual	❌	✅ Mobile	Absolute beginners	0	

Key Findings (NEW)
- TradeNote is the most mature pure open-source journal but uses MongoDB (document store), which is suboptimal for analytical queries. It has no native AI. 
- TradeTally is the closest to a "modern TraderVue killer" with Docker, PostgreSQL, and Gemini AI—but self-hosting requires a Finnhub API key for real-time quotes. 
- OpenTradex is not a journal per se but a cockpit; it has no built-in journaling schema, but its 12 connectors and local-first architecture make it the best quant starting point. 
- Deltalytix has the most advanced AI agent layer (AI Coach, pattern recognition, sentiment analysis) but its CC BY-NC license prohibits commercial use, and self-hosting is "currently in development" as of Q2 2026. 
- OpenBB Terminal is an analytics powerhouse (Sharpe, VaR, options Greeks, backtesting) but requires Python fluency and has no trade-entry UI. 

---

2. DECISION MATRIX: Pick Components by Trader Type

Matrix A: Journal Core by Trader Profile

Trader Type	Recommended Core	Database	Why	
Non-Dev Beginner	TradeTally (Docker)	PostgreSQL	One-command Docker setup, modern UI, iOS app, built-in AI	
Privacy-First / Paranoid	TradeNote (self-host)	MongoDB + SQLite backup	GPL-3.0, no telemetry, runs offline, community-audited	
Prop Firm Challenge	Deltalytix (cloud now) / TradeTally + custom CSV	PostgreSQL	Deltalytix has FTMO/Topstep rule tracking; TradeTally has multi-broker CSV	
Forex-Only	Myfxbook (cloud) + TradeNote backup	N/A / MongoDB	Myfxbook auto-syncs MT4/MT5 unlimited for free	
Quant / Developer	OpenTradex + custom schema	DuckDB + SQLite	CLI-first, 12 market connectors, bring-your-own-model AI	
Options Heavy	TradeTally + OpenBB Terminal	PostgreSQL + DuckDB	TradeTally parses options contracts; OpenBB calculates Greeks/VaR	
Swing / Low Volume	TraderVue Free or TradesViz Free	Cloud	<100 trades/mo, no setup hassle	
AI-Native / LLM Hacker	OpenTradex + LangGraph + Ollama	DuckDB + Polars	Graph-based agent workflows, local LLM, code-first	

Matrix B: Data Ingestion Layer

Source	Method	Tooling	Cost	Reliability	
IBKR	API (ib_insync)	Python + TWS/IB Gateway	Free	⭐⭐⭐⭐⭐ Best for multi-asset	
Schwab	API (post-TDA)	OAuth 2.0 REST	Free	⭐⭐⭐ Migration was rough; docs lag Alpaca	
Alpaca	API REST/WebSocket	Official SDKs (Py/JS/Go/C#)	Free	⭐⭐⭐⭐⭐ Cleanest API; US equities + crypto only	
cTrader	Open API	OAuth Public Client ID	Free	⭐⭐⭐⭐ Best free forex API	
Tradovate	API	REST	PAID	⭐⭐⭐ S1 incorrectly said free; API access requires subscription	
TradingView	Webhook	Google Apps Script / Flask	Free	⭐⭐⭐⭐ Requires paid TV plan for webhooks	
Prop Firms (FTMO/TFT/MFF)	NO API	Headless browser (Puppeteer/Playwright) + CSV	Free	⭐⭐ Fragile; requires scraping discipline	
Generic CSV	Manual	Polars/DuckDB for normalization	Free	⭐⭐⭐⭐ Depends on broker export quality	

Matrix C: AI & Voice Input Stack

Component	Option	Best For	Hardware	Accuracy	Setup	
Local LLM	Ollama + Qwen3 8B	General analysis, pattern chat	8GB+ VRAM or M-series Mac	High	1-command	
Local LLM	Ollama + Gemma 3 4B	Lightweight, edge devices	4GB RAM	Good	1-command	
Local LLM	Ollama + nomic-embed-text	RAG / trade similarity search	Minimal	N/A	1-command	
Vision / OCR	Ollama + llava / moondream	Screenshot analysis	4GB+ VRAM	Medium-High	1-command	
Speech-to-Text	Whisper.cpp	Best speed/accuracy ratio	CPU/GPU	High	Small model (39MB)	
Speech-to-Text	Vosk	Low-end hardware, offline	CPU only	Good	Very lightweight	
Speech-to-Text	Browser Speech API	Zero-setup, web journal	Any	Medium	Zero	
Screenshot Capture	mss + dxcam (Python)	144fps capture, low overhead	Any	N/A	pip install	
OCR (legacy)	Tesseract 5	Text extraction, forms	Any	Medium	Heavy config	
OCR (modern)	PaddleOCR/Surya	Handwritten, multi-language	GPU preferred	High	Moderate	
Workflow Automation	Python scripts preferred	NO n8n — use scripts	Any	N/A	Python	

Matrix D: Database & Analytics Backend

Database	Role	Best For	Memory	Speed	SQL	
SQLite	CRUD / single-user journal	Embedded, zero-config	Minimal	Fast	Yes	
PostgreSQL	Multi-user / structured journal	TradeTally, Deltalytix, Ghostfolio	Medium	Fast	Yes	
MongoDB	Document store / flexible schema	TradeNote, unstructured notes	Medium	Medium	No	
DuckDB	Analytical warehouse	MFE/MAE, win-rate by setup, large history	Very low	Very fast	Yes	
Polars	DataFrame transformations	Complex ETL, broker CSV normalization	Low-Medium	Very fast	No (expr API)	

---

3. ADDITIONS & CORRECTIONS TO YOUR SOURCES

S1 (ChatGPT) — Corrections

Claim	Status	Correction	
"Tradovate sync" in TradeTally	⚠️ Partially true	TradeTally lists "ProjectX" but Tradovate API itself is paid, not free. CSV import is the free path.	
"OpenTradex AI cockpit for developers"	✅ Accurate	Confirmed 12 connectors, local-first, paper-by-default, BYO model.	
"OpenBB analytics backbone"	⚠️ Misleading	OpenBB is a research terminal, not a trade journal. No trade-entry UI. Best used as a data layer alongside a journal.	
"Recommended stack: TradeTally UI + PostgreSQL+DuckDB + Ollama+Qwen3 + Obsidian + n8n"	✅ Solid	NO n8n — use Python scripts instead. This is the best non-dev power-user stack minus n8n. Add Syncthing for mobile sync.	
"Three build paths"	⚠️ Oversimplified	Missing the prop firm path and forex-only path.	

S2 (Voice/Screenshots/Architecture) — Additions

Component	S2 Claim	Addition / Correction	
Whisper.cpp	"Best free/local"	✅ Confirmed. Default for speed/accuracy. Vosk wins only on <2GB RAM systems.	
Vosk	"Lighter"	✅ True, but accuracy degrades with noise. Use only for old hardware.	
Browser Speech API	"Zero-setup"	✅ True, but requires internet (cloud STT in most browsers). Not truly local.	
mss+dxcam	"144fps"	✅ True for Windows DXcam; mss is cross-platform but lower FPS on macOS/Linux.	
OCR	Tesseract/Paddle/Surya	Missing: Ollama vision models (llava/moondream) can do screenshot→JSON extraction in one step, no separate OCR needed.	
DuckDB	"For analytics"	✅ True. Add: DuckDB can query Parquet/CSV directly without loading into memory.	
SQLite	"For CRUD"	✅ True. Add: SQLite + litestream = free continuous backup to S3.	
Polars	"Complex analysis"	✅ True. Add: Use Polars for normalizing broker CSVs before DuckDB analytics.	
Syncthing	"P2P free sync"	⚠️ Critical caveat: Syncthing cannot safely sync live SQLite/PostgreSQL files. You must export .dump or .parquet snapshots first.	

S3 (Broker APIs/Prop Firms) — Corrections

Claim	Status	Correction	
"Tradovate (paid API access)"	✅ Accurate	S3 correctly identified this; S1 incorrectly implied free sync.	
"cTrader (best free forex API)"	✅ Accurate	Confirmed free OAuth Public Client ID from Spotware.	
"Schwab API (free)"	✅ Accurate	But migration from TDA broke all legacy integrations in Sep 2024. New projects should start elsewhere.	
"Alpaca (free crypto/stocks)"	✅ Accurate	Best free-to-start API. 200 req/min free tier, 1,000/min funded.	
"TradingView webhooks"	⚠️ Partially true	Requires paid TradingView plan (Essential+). Free plans only get email alerts.	
"Prop firms have NO APIs"	✅ Accurate	Confirmed: FTMO, TFT, MFF only offer CSV export via client portal. Headless browser scraping is the only automation path.	
"Unified trade schema"	✅ Needed	Suggest: Use Polars to normalize all broker CSVs into a canonical schema before DuckDB ingestion.	

---

4. TOP 3 RECOMMENDED STACKS (Ranked) — n8n replaced with Python scripts

🥇 STACK 1: "The Sovereign Trader" 
For privacy-first day traders who want AI without cloud lock-in.

Layer	Tool	Role	
Journal UI	TradeTally (self-hosted)	Trade entry, options/futures support, Gemini AI insights	
Database	PostgreSQL 15	Structured trade storage, multi-account	
Analytics	DuckDB (sidecar)	MFE/MAE, win-rate by setup, session analysis	
Local AI	Ollama + Qwen3 8B	Pattern chat, trade review, psychology coaching	
Notes	Obsidian + Dataview plugin	Daily brain dumps linked to trade IDs	
Voice	Whisper.cpp (tiny model)	Post-session voice memos → text	
Screenshots	mss + Ollama llava	Auto-tag chart screenshots with setup type	
Sync	Syncthing (snapshot exports)	P2P sync of DuckDB Parquet exports + Obsidian vault	
Automation	Python scripts	Broker CSV → normalize → PostgreSQL pipeline	
Deployment	Docker Compose	Single docker-compose up on laptop or mini-PC	

---

🥈 STACK 2: "The Prop Firm Survivor"
For traders passing FTMO/TFT/Apex who need rule-tracking and multi-account normalization.

Layer	Tool	Role	
Journal UI	TradeNote + custom dashboard	Self-hosted, no caps, prop-firm CSV templates	
Database	SQLite (per account) + MongoDB (master)	Account isolation + unified view	
Analytics	Polars + DuckDB	Normalize 5 prop firm CSV formats → unified schema	
Local AI	Ollama + Gemma 3 4B	Lightweight; runs on trading laptop while platform is open	
Screenshots	dxcam + PaddleOCR	Capture platform UI, extract fill prices	
Sync	rclone (encrypted)	Backup SQLite files to Backblaze B2	
Automation	Puppeteer/Playwright	Headless login to prop firm portals, auto-download CSVs	
Rule Tracking	Custom Python scripts	Daily drawdown check, consistency rule validator	

---

🥉 STACK 3: "The Quant's Cockpit"
For developers building a custom AI-native trading command center.

Layer	Tool	Role	
Cockpit	OpenTradex (npm/CLI)	Multi-market scanner, paper-first execution	
Journal Engine	Custom FastAPI + SQLite	Lightweight trade logging API	
Database	DuckDB (primary)	All analytics, backtest results, market context	
DataFrame	Polars	ETL, feature engineering, broker normalization	
AI Orchestration	LangGraph + Ollama	Stateful agent workflows: scan → filter → journal → review	
Market Data	Polygon.io free tier	15-min delayed data for context	
Broker Execution	Alpaca API (paper)	US equities/crypto; cleanest API for devs	
Forex	cTrader Open API	Free forex data + execution via Spotware	
Deployment	Docker Compose + Electron	Local desktop app feel, web dashboard for analytics	

---

5. COST REALITY CHECK: True 5-Year TCO

Stack	Year 1	Year 2	Year 3	Year 4	Year 5	Total	
Sovereign (Stack 1)	0	0	0	0	0	0 + hardware	
Prop Survivor (Stack 2)	0	0	0	0	0	0 + B2 backup pennies	
Quant Cockpit (Stack 3)	0	348	348	348	348	1,392 (Polygon real-time)	
vs. TraderVue Silver	348	348	348	348	348	1,740	
vs. TradeZella	588	588	588	588	588	2,940	
vs. JournalPlus	159	0	0	0	0	159	

---

6. CRITICAL GAPS & MISSING PIECES (NEW)

1. No open-source journal has true real-time broker sync for free. All "sync" is CSV-based or requires paid API tiers (Tradovate).
2. MongoDB (TradeNote) is a dead-end for analytics. You will eventually ETL to DuckDB/PostgreSQL for performance. Plan for this migration.
3. Syncthing + live databases = corruption. Never sync .db or .wal files. Export snapshots only.
4. Whisper.cpp on CPU is fast enough for voice memos but too slow for real-time dictation during trading. Use Browser Speech API for live voice commands, Whisper.cpp for post-session transcription.
5. Ollama vision models (llava) are mediocre at reading chart screenshots. For production OCR, use PaddleOCR or Surya, then feed text to Ollama.
6. n8n is not used — Python scripts replace it.
7. Prop firm rule tracking is underserved. No open-source tool auto-validates FTMO consistency rules or max daily loss. This requires custom Python/Polars logic.
8. Qwen3 8B on Ollama needs 6GB VRAM. If you only have CPU/integrated graphics, use Gemma 3 4B or Phi-4 mini for acceptable latency.

---

7. BROKER API REALITY MATRIX (Updated S3)

Broker/API	Free?	Asset Classes	Rate Limit	Best For	Gotchas	
Alpaca	✅	Stocks, Options, Crypto	200/min free	US algo devs	Non-US needs 30K min	
IBKR (ib_insync)	✅	Global multi-asset	50/10s	Institutional power	Requires TWS/Gateway running	
Schwab	✅	US equities, options	120/min	Legacy TDA users	OAuth rewrite required post-migration	
cTrader Open API	✅	Forex, CFDs	Unpublished	Forex automation	Broker-dependent execution	
Tradovate	❌ Paid	Futures	Unpublished	Futures traders	API access requires paid plan	
Polygon.io	⚠️ Delayed free	Market data only	5/min free	Data layer	Execution requires separate broker	
TradingView	❌ Webhooks paid	Alert routing	N/A	Signal generation	Essential plan minimum	
Prop Firms	❌ No API	N/A	N/A	Challenge tracking	CSV + headless browser only	

---

8. QUICK-START COMMAND CHEAT SHEET (adapted for scripts, no n8n)

```bash
# STACK 1: Sovereign Trader
git clone https://github.com/GeneBO98/tradetally.git && cd tradetally
echo "FINNHUB_API_KEY=your_key" > .env
echo "GEMINI_API_KEY=your_key" >> .env
docker-compose up -d

# STACK 2: Prop Survivor
ollama pull gemma3:4b
ollama pull nomic-embed-text

# STACK 3: Quant Cockpit
npm install -g opentradex
opentradex onboard
# Build LangGraph workflow in Python
pip install langgraph ollama duckdb polars
```
