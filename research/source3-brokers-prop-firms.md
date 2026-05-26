# Source 3: Broker APIs, Prop Firms & Multi-Broker Aggregation

## Broker API Landscape (Free Access)

### Interactive Brokers (IBKR)
- **IB Gateway / TWS API**: Free, local. Python ib_insync or native API. Full trade history, positions, market data via socket connection. Best-in-class free API for a real broker.
- **Client Portal Web API**: REST API, also free. Good for polling trade history periodically.
- *Limitation*: Requires running IB Gateway locally. No cloud API without a paid market data subscription.

### Tradovate
- **REST + WebSocket API**: Free with funded account. Python tradovate-api wrapper available. Real-time position updates, trade history export.
- *Limitation*: API keys only on paid plans ($50+/mo for API access).

### NinjaTrader
- **NinjaScript + API**: Local only. Trade history exportable via CSV. No official REST API. Community-built connectors exist but fragile.
- *Workaround*: CSV export + scheduled import script.

### MetaTrader 4/5
- **MT4/5 Web API**: Broker-specific. Most brokers provide read-only API access. Python-MT5 connector for trade history.
- *Limitation*: Each broker has different endpoint. No universal adapter.

### cTrader
- **cTrader REST API**: Free with any cTrader broker account. Clean trade history, position data, account info. Best free API among forex platforms.
- **cTrader FIX API**: For high-frequency. Overkill for journaling.

### TradingView
- **Webhook Alerts**: Free for basic plan. Send trade signals to your journal webhook via JSON payload. Ideal for automated trade logging from chart-based entries.

### Schwab / TD Ameritrade
- **Schwab API**: Free. Replaced TD Ameritrade API. OAuth-based REST. Full trade history, positions, account data. Good for US equities/options traders.

### Alpaca (Crypto + Stocks)
- **Free tier**: Paper trading + live with funded account. REST + WebSocket. Clean API, good docs. Best for crypto journal integration.

## Prop Firm Connections

### FTMO
- **No public API**. Trade data export via CSV (MyFXBook-style statements). Must manually download or scrape.
- *Free approach*: FTMO provides downloadable trade history in CSV format via their dashboard. Schedule a script to download daily.

### The Funded Trader (TFT)
- **No API**. Dashboard export to CSV. Similar to FTMO.

### MFF (My Forex Funds)
- **No API**. CSV export from dashboard.

### Prop Firm Aggregation Strategy
- Since no prop firm offers APIs, the approach is:
  1. Scheduled headless browser login + CSV download (Playwright/Puppeteer)
  2. CSV parser that normalizes to a unified trade schema
  3. Manual entry fallback for one-off trades
  4. *Privacy note*: This stores prop firm credentials locally. Encrypt at rest.

## Multi-Broker Aggregation Schema

### Unified Trade Record
```json
{
  "trade_id": "uuid",
  "source": "ibkr|tradovate|ftmo_csv|manual",
  "broker_account": "acct_name",
  "asset_class": "futures|forex|stock|crypto|option",
  "instrument": "ES|EURUSD|AAPL|BTC",
  "direction": "long|short",
  "entry_price": 5032.50,
  "exit_price": 5060.00,
  "quantity": 2,
  "entry_time": "2026-05-24T09:31:00Z",
  "exit_time": "2026-05-24T10:15:00Z",
  "stop_loss": 5018.00,
  "take_profit": 5060.00,
  "fees": 3.50,
  "pnl": 550.00,
  "pnl_points": 27.5,
  "tags": ["breakout", "es", "morning_session"],
  "screenshots": ["2026-05-24_0931_entry.png", "2026-05-24_1015_exit.png"]
}
```

### Cross-Broker Performance Comparison
- Win rate by broker
- Average R:R by asset class across all accounts
- Total exposure across all open positions
- Daily P&L aggregation from all sources
- Monthly Sharpe ratio (broker-level and consolidated)

### Free Aggregation Tools
- **n8n** (self-hosted): Visual workflow automation. Schedule CSV imports, transform data, insert into DB. Free.
- **Python scheduler** (APScheduler): Custom scripts per broker, runs on cron. More flexible but more work.
- **Obsidian + Dataview**: If using Obsidian as the journal frontend, Dataview queries can aggregate trades stored as markdown frontmatter.

## Cost Comparison

| Component | Best Free Option | Paid Upgrade | Why Upgrade |
|-----------|-----------------|--------------|-------------|
| Trade storage | SQLite + DuckDB | PostgreSQL | Concurrency, networking |
| Voice input | Whisper.cpp | Deepgram API | Cloud accuracy |
| AI analysis | Ollama (local Qwen3) | Claude API | Complex reasoning |
| Screenshot OCR | PaddleOCR | Google Cloud Vision | Speed at scale |
| Automation | n8n (self-hosted) | n8n cloud | Maintenance |
| Sync | Syncthing | Dropbox/Drive | Ease of use |
| Charts | TradingView Lite | TradingView Pro | More indicators |
