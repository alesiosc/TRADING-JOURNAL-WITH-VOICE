# NT8 Integration — TradeJournalConnector

Connects NinjaTrader 8 directly to your Trading Journal.  
Place the indicator on any chart → it auto-detects entries, exits, SL moves,  
partial closes, and BE adjustments → sends everything to the journal +  
auto-captures chart screenshots.

## Installation

1. **Copy the indicator file:**
   ```
   Copy  brokers/nt8_indicator/TradeJournalConnector.cs
     To:  Documents\NinjaTrader 8\bin\Custom\Indicators\
   ```

2. **Compile in NT8:**
   - Open NT8
   - Go to New → NinjaScript Editor
   - Right-click → Compile (or press F5)
   - Fix any compilation errors (usually none)

3. **Add to chart:**
   - Right-click chart → Indicators
   - Search for "TradeJournalConnector"
   - Add it
   - Configure:
     - **Journal URL**: `http://localhost:8000` (or wherever the journal runs)
     - **Account Name**: Your NT8 account name (e.g. Sim101)
     - **Auto Screenshot**: ✓ Enabled
     - **Debug Logging**: ✓ (during setup, disable later)

## What It Does Automatically

| Action | Journal Event |
|--------|--------------|
| You click Buy → trade fills | Entry trade created, screenshot captured |
| You click Sell to close | Trade closed with P&L, screenshot captured |
| Move stop loss to breakeven | Modify event logged, journal entry created |
| Take partial profits | Partial close logged as trade leg |
| Position fully closed | P&L auto-calculated, trade marked closed |
| Chart screenshot | PNG saved to `Documents/TradingJournalScreenshots/` |

## Test It

After adding the indicator:

1. Make sure the journal backend is running:
   ```
   http://localhost:8000/api/nt8/status
   ```
   Should return `{"status": "ok"}`

2. Take a trade in NT8 → the journal receives it instantly.
3. Check the journal Trades page → your NT8 trade appears.
4. Check `Documents/TradingJournalScreenshots/` for chart screenshots.

## Troubleshooting

- **"Journal send failed" in NT8 log** → Backend not running or wrong URL
- **No trades appearing** → Check the URL matches your journal's port
- **No screenshots** → `Auto Screenshot` must be enabled, chart must be visible
- **Double entries** → Only place ONE indicator per chart

## NT8 Requirements

- NinjaTrader 8.1+
- .NET Framework 4.8+
- The journal backend must be running before NT8 sends trades
