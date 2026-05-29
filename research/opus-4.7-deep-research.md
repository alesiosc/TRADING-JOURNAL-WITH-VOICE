# Opus 4.7 / Anything.com — Deep Research: GhostJournal

**Source:** Anything.com (Opus 4.7)
**Date:** ~25 May 2026
**Topic:** Free, self-hosted, local-first trading journal with AI features

---

## 1. Trade Data Capture — Manual & Automated

| Platform | Recommended Tool / API | Complexity |
|----------|----------------------|------------|
| Interactive Brokers | ib_insync (Python) via IB Gateway | Moderate |
| Schwab/Ameritrade | schwab-py (OAuth 2.0 flow) | Moderate |
| MetaTrader 4/5 | MetaTrader5 Python Package | Easy |
| Tradovate/Ninja | Tradovate API (Standard REST) | Moderate |
| Prop Firms | Custom Python Parsers for [FTMO/MFF CSVs] | Easy |

### Manual Entry UI (High-Fidelity SaaS Implementation)
- **Hotkeys:** Use react-hotkeys-hook for Ctrl+L (New Long) and Ctrl+S (New Short)
- **Pill Taxonomy:** Tickers ($ES, $NQ) rendered as Outline Pills (border-gray-200). Status (e.g. "In-Progress") uses Status Pill with 6px orange dot

## 2. Real-Time Metrics & Analytics

- **Storage Engine:** DuckDB (v1.2+) — query multi-gigabyte trade histories sub-second
- **Rolling Metrics:** SQL WINDOW functions for P&L and Drawdown without re-scanning
- **Free Metrics Library:** QuantStats (Python) — Sharpe, Sortino, Tearsheets
- **Complexity:** Moderate (requires SQL proficiency)

## 3. Trade Screenshotting — Real-Time Capture

- **Auto-Capture:** PyAutoGUI to trigger screenshots on trade execution
- **Modern OCR:** Surya — outperforms Tesseract for technical chart text (P&L, entry prices)
- **Annotation:** Fabric.js for web-based canvas overlay (mark "Double Bottom" or "FVP")
- **Complexity:** Moderate

## 4. AI Integrations — Free Tier / Local

- **Local Brain:** Ollama running Qwen2.5-Coder (7B) or Llama 3.2
- **AI Narrative:** Feed last 5 trades (JSON) → LLM prompt: "Identify the common psychological trigger in these losses"
- **Free Cloud Fallback:** Google Gemini 1.5 Flash API (15 RPM / 1M TPM free tier)
- **Complexity:** Complex (managing local model weights + context windows)

## 5. Multi-Broker / Multi-Account Aggregation

**Unified Schema:**
```sql
CREATE TABLE unified_trades (
    trade_id UUID PRIMARY KEY,
    broker_source TEXT,       -- 'IBKR', 'FTMO'
    asset_class TEXT,         -- 'FUTURE', 'CRYPTO'
    entry_time TIMESTAMP,
    notional_value DECIMAL,
    risk_pct DECIMAL
);
```

- **Normalization:** Pandas for data cleaning
- **Asset Classes:** CCXT for Crypto, YFinance for free historical stock/futures pricing

## 6. Architecture & Build Options

**Recommended: "Ghost-Local" Web App**
- **Frontend:** React + Tailwind CSS
- **Database:** ElectricSQL or RxDB for local-first sync
- **Desktop Wrapper:** Tauri (v2.0) — lighter than Electron, filesystem access for screenshots
- **Sync:** Syncthing for database file sync across devices
- **Complexity:** Moderate

### UI Design System
- White background (#FFFFFF)
- Borders: #E5E7EB
- Font: Inter
- Pill taxonomy for all tags/chips
- Feature Cards with ghost border: `bg-white rounded-xl border border-[#E5E7EB] p-6`

## 7. Existing Free Trading Journals

| Project | Stars | Strengths | Weaknesses |
|---------|-------|-----------|------------|
| GhostTrader | ~1.2k | Good UI, local-first | No AI integration |
| OpenJournal | ~800 | Massive broker support | Python/Tkinter (dated UI) |
| TradeVis | ~500 | Great charting | Requires manual CSV |

**The Gap:** No current open-source project combines Local LLM review with High-Fidelity "Ghost" UI aesthetics.

## 8. Voice Input Deep Dive

- **Engine:** Whisper.cpp — transcribes 30s audio in <1s on modern laptop
- **Command Parser:** RegEx + LLM Intent Extraction
  - "Long ES 2 contracts at 5032.50" → `{"action": "BUY", "ticker": "ES", "qty": 2, "price": 5032.50}`
- **Complexity:** Complex (audio buffer management)

## Edge Cases & Mitigation

- **API Deprecation:** Use "Bridge" architecture — capture logic separated from core journal
- **AI Rate Limits:** Local fallback (Ollama) when cloud API throttles
- **Data Privacy:** Strip P&L dollar amounts before sending to cloud AI; send R-multiple and Tick data only

## UI Implementation Pattern

```jsx
<div className="bg-white rounded-xl border border-[#E5E7EB] p-6">
  <div className="flex justify-between items-start mb-4">
    <div>
      <h3 className="text-lg font-semibold text-[#111827]">Long Entry: $ES</h3>
      <p className="text-sm text-[#6B7280]">Executed via Interactive Brokers</p>
    </div>
    <button className="bg-[#EFF6FF] text-[#2563EB] rounded-full px-3 py-1.5 text-sm font-medium inline-flex items-center gap-1.5 hover:bg-blue-100 transition-colors">
      <Sparkles size={14} />
      AI Review
    </button>
  </div>
  <div className="mt-4 space-y-1">
    <div className="text-sm text-[#4B5563]"><span className="text-gray-400 mr-2">-</span> 5-minute fair value gap fill</div>
    <div className="text-sm text-[#4B5563]"><span className="text-gray-400 mr-2">-</span> Volume delta was positive on entry</div>
  </div>
</div>
```

---

*This research was used to inform the GhostJournal design direction — pill taxonomy, High-Fidelity SaaS UI, local-first architecture, and the "bridge" pattern for broker connectors.*
