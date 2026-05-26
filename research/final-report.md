# Free All-Purpose Trading Journal — Mid 2026 Deep Research

**Sources:** ChatGPT (browser), Voice/Screenshot/Architecture analysis, Broker/Prop Firm analysis
**Compiled:** 24 May 2026

---

## Comparison Table: Free/Open-Source Trading Journal Platforms

| Feature | TradeNote | TradeTally | OpenTradex | OpenBB | Obsidian + Dataview |
|---------|-----------|------------|------------|--------|---------------------|
| **Type** | Pure journal | Modern journal | AI cockpit | Analytics engine | Note + query |
| **Price** | Free (self-host) | Free (Docker) | Free (local) | Free (self-host) | Free |
| **Deployment** | Docker/local | Docker | Local binary | Docker/Python | Desktop app |
| **Broker APIs** | Manual import | IBKR, Schwab, Webull, Tradovate, TradingView | Custom connectors | Market data only | Manual + plugins |
| **Multi-asset** | Stocks, FX, futures | All | All | Stocks, macro | Any (manual) |
| **AI Integration** | Minimal | Basic AI insights | AI copilot (built-in) | Research AI | Ollama plugin |
| **Screenshots** | Yes | No native | Chart analysis | No | Via plugin |
| **Voice Input** | No | No | No | No | Plugin possible |
| **Real-time metrics** | Basic | Good | Advanced | Excellent | Dataview queries |
| **Automation** | None | Webhooks | Agent built-in | API-driven | Community plugins |
| **Mobile** | Web responsive | Web responsive | No | No | Yes (mobile app) |
| **Best for** | Discretionary traders who want simplicity | All-purpose free journal | Developer/quants building from scratch | Analytics-heavy research | Note-centric traders |
| **Setup complexity** | Low | Medium | High | Medium | Low |

---

## Component Decision Matrix

### Data Ingestion

| Broker/Platform | Free Method | Complexity | Reliability |
|----------------|-------------|-----------|-------------|
| **IBKR** | ib_insync (Python) | Medium | High |
| **Tradovate** | REST API (paid acc req) | Medium | High |
| **NinjaTrader** | CSV export + scheduler | Low | Medium |
| **MT4/5** | python-mt5 connector | Medium | Medium |
| **cTrader** | REST API (free) | Low | High |
| **TradingView** | Webhook alerts | Low | High |
| **Schwab** | Schwab API (free) | Medium | High |
| **Alpaca** | REST API (free) | Low | High |
| **FTMO/MFF/TFT** | Headless browser + CSV | High | Low (breaks on site changes) |

### Database

| Engine | Best For | Pros | Cons |
|--------|----------|------|------|
| **SQLite** | Trade CRUD, single-user | Zero-config, portable | No concurrency |
| **PostgreSQL** | Multi-user, server setup | Full features, networking | Setup overhead |
| **DuckDB** | Analytics, aggregations | 10x faster than SQLite | Not for writes |
| **Polars** | Complex analysis, ML features | Pandas-speed on large data | Memory-heavy |

### AI

| Option | Cost | Quality | Privacy | Setup |
|--------|------|---------|---------|-------|
| **Ollama + Qwen3 (local)** | Free (compute) | Good | Full | Medium |
| **Gemini API free tier** | Free (60 req/min) | Excellent | Cloud | Low |
| **Grok free tier** | Free (10 req/hr) | Good | Cloud | Low |
| **OpenRouter free models** | Free (rate-limited) | Varies | Cloud | Low |
| **LM Studio + Llama 4** | Free (compute) | Good (multimodal) | Full | Low |

### Screenshot + OCR

| Tool | Cost | Accuracy | Speed | Setup |
|------|------|----------|-------|-------|
| **mss + Pillow** | Free | N/A (capture) | Fast | Low |
| **dxcam (DXGI)** | Free | N/A (capture) | 144fps | Low |
| **Tesseract 5** | Free | ~90% | Fast | Low |
| **PaddleOCR** | Free | ~95% | Medium | Medium |
| **Surya** | Free | ~98% | Slow (GPU) | High |

### Voice Input

| Tool | Cost | Accuracy | Latency | Offline |
|------|------|----------|---------|---------|
| **Whisper.cpp** | Free | ~98% | <1s | Yes |
| **Vosk** | Free | ~90% | <0.5s | Yes |
| **Browser Speech API** | Free | ~95% | Real-time | No (browser) |

---

## Top 3 Recommended Stacks

### Stack 1: Best All-Rounder (Recommended)

| Layer | Tool | Why |
|-------|------|-----|
| **UI** | TradeTally (Docker) | Best free journal UI, broker sync built-in |
| **Database** | PostgreSQL + DuckDB | CRUD + analytics split |
| **AI** | Ollama + Qwen3 | Local, free, private |
| **Voice** | Browser Speech API | Zero-setup for web UI |
| **Screenshots** | mss + PaddleOCR | Fast capture + good OCR |
| **Automation** | n8n | Visual workflows for broker imports |
| **Notes** | Obsidian + Dataview | Deep analysis + recall |
| **Deployment** | Docker Compose | One-command setup |

**Trader type:** Most traders. Balances capability with setup effort.

### Stack 2: Pure Open-Source (Simplest)

| Layer | Tool |
|-------|------|
| **UI** | TradeNote |
| **Database** | SQLite |
| **AI** | Gemini API (free tier) |
| **Voice** | Browser Speech API |
| **Screenshots** | mss + Tesseract |
| **Automation** | Python cron scripts |
| **Notes** | TradeNote built-in |
| **Deployment** | Docker (single container) |

**Trader type:** Discretionary traders wanting simplicity. Minimal setup, still capable.

### Stack 3: Power User / Quant

| Layer | Tool |
|-------|------|
| **UI** | Custom (Next.js + TradingView Lite) |
| **Database** | PostgreSQL + DuckDB + Parquet |
| **AI** | Ollama + Qwen3 + LangGraph agents |
| **Voice** | Whisper.cpp (hotkey-activated) |
| **Screenshots** | dxcam + Surya |
| **Automation** | n8n + Python |
| **Research** | OpenBB |
| **Deployment** | Docker Compose + Syncthing |

**Trader type:** Developers, quants, automation-heavy. Full control, maximum capability.

---

## Decision Matrix: Pick Your Path

```
Q1: How technical are you?
├─ Not technical → Stack 1 (pre-configured Docker)
├─ Comfortable with CLI → Stack 2 (TradeNote + SQLite)
└─ Developer → Stack 3 (custom everything)

Q2: What do you trade?
├─ Futures + Forex → IBKR/cTrader connectors needed
├─ Stocks + Options → Schwab/Tradovate integration
└─ All of the above → Unified schema (Stack 1 or 3)

Q3: How important is AI?
├─ Nice-to-have → Use TradeTally's built-in AI insights
├─ Core feature → Ollama + Qwen3 local (Stack 1)
└─ Must have agents → LangGraph + n8n (Stack 3)

Q4: Voice input needed?
├─ Occasional → Browser Speech API (zero setup)
├─ Daily → Whisper.cpp hotkey (best accuracy)
└─ Hands-free → Whisper + wake-word detection

Q5: Privacy concern level?
├─ Low → Gemini/Grok free tiers fine
├─ Medium → Ollama local, cloud for heavy tasks
└─ High → Everything local (Ollama + Whisper + local DB)
```

---

## What's Missing & Future Outlook

### Gaps in the Free Ecosystem
1. **No unified free journal** that does everything — you must assemble components
2. **Prop firm APIs don't exist** — headless browser scraping is fragile
3. **Mobile experience is weak** — no good free mobile trading journal app
4. **Voice integration is DIY** — no trading journal has built-in voice input
5. **Real-time multi-broker aggregation** requires custom build

### What to Watch
- **OpenTradex** is the most ambitious project — if it matures, it could become the single unified platform
- **TradeTally** is actively adding features and has the best trajectory for a "set and forget" solution
- **Local LLMs** (Qwen3, Llama 4) are crossing the quality threshold where they're genuinely useful for trade analysis
- **Whisper.cpp** v1.7+ with streaming makes real-time voice journaling practical

### Verdict
For mid-2026, the best free trading journal is **not a single app** — it's a modular stack with TradeTally or TradeNote as the UI, PostgreSQL+DuckDB for storage, Ollama+Qwen3 for AI, and n8n for glue. The component ecosystem is mature enough that a moderately technical trader can assemble a system that rivals paid journals ($20-100/mo) for zero ongoing cost.
