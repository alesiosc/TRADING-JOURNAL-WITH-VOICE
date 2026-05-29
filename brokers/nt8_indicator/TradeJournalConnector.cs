//==============================================================================
// TradeJournalConnector — NinjaTrader 8 Indicator
// Automatically sends trades to your local Trading Journal.
//
// Place this on any chart. It monitors executions and position changes,
// sends trade data via HTTP to the journal backend, and auto-captures
// chart screenshots on entry/exit/modify events.
//
// Installation:
//   1. Copy this file to: Documents\NinjaTrader 8\bin\Custom\Indicators\
//   2. Compile in NT8 (F5 / right-click → Compile)
//   3. Add to chart: Indicators → TradeJournalConnector
//   4. Configure the Journal URL (default: http://localhost:8000)
//
// Events sent:
//   Entry (long/short)  →  POST /api/nt8/trade  {event:"entry", ...}
//   Full exit           →  POST /api/nt8/trade  {event:"exit", ...}
//   Partial close       →  POST /api/nt8/trade  {event:"partial_close", ...}
//   SL/TP modify        →  POST /api/nt8/trade  {event:"modify", ...}
//   Screenshot trigger  →  POST /api/nt8/screenshot
//==============================================================================

#region Using declarations
using System;
using System.IO;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using Newtonsoft.Json;
using NinjaTrader.Cbi;
using NinjaTrader.Data;
using NinjaTrader.Gui;
using NinjaTrader.Gui.Chart;
using NinjaTrader.NinjaScript;
using NinjaTrader.NinjaScript.Indicators;
#endregion

namespace NinjaTrader.NinjaScript.Indicators
{
    public class TradeJournalConnector : Indicator
    {
        private HttpClient _http;
        private string _journalUrl;
        private double _lastEntryPrice;
        private int _lastQuantity;
        private string _lastDirection;
        private bool _hasOpenPosition;

        // ── User-configurable properties ──

        [NinjaScriptProperty]
        [Display(Name = "Journal URL", Order = 1, GroupName = "Journal Connection")]
        public string JournalUrl { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Account Name", Order = 2, GroupName = "Journal Connection")]
        public string AccountName { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Auto Screenshot on Events", Order = 3, GroupName = "Journal Connection")]
        public bool AutoScreenshot { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Send Journal Notes", Order = 4, GroupName = "Journal Connection")]
        public bool SendNotes { get; set; }

        [NinjaScriptProperty]
        [Display(Name = "Enable Debug Logging", Order = 5, GroupName = "Journal Connection")]
        public bool DebugLogging { get; set; }

        // ── Initialization ──

        protected override void OnStateChange()
        {
            if (State == State.SetDefaults)
            {
                Description = @"Sends trades to your local Trading Journal. Monitors executions, position changes, and auto-captures screenshots.";
                Name = "TradeJournalConnector";
                IsOverlay = true;
                DisplayInDataBox = false;
                DrawOnPricePanel = true;
                DrawHorizontalGridLines = false;
                DrawVerticalGridLines = false;
                PaintPriceMarkers = false;
                IsSuspendedWhileInactive = true;

                // Defaults
                JournalUrl = "http://localhost:8000";
                AccountName = "Sim101";
                AutoScreenshot = true;
                SendNotes = true;
                DebugLogging = false;
            }
            else if (State == State.Configure)
            {
                // Runs on chart, no additional data required
            }
            else if (State == State.DataLoaded)
            {
                _http = new HttpClient();
                _http.Timeout = TimeSpan.FromSeconds(5);
                _hasOpenPosition = false;
                Log("TradeJournalConnector initialized — sending to " + JournalUrl);
            }
            else if (State == State.Terminated)
            {
                if (_http != null)
                {
                    _http.Dispose();
                    _http = null;
                }
            }
        }

        // ── Bar Update (used for screenshots on new bars) ──

        protected override void OnBarUpdate()
        {
            // No trading logic needed — executions are handled in OnExecutionUpdate
        }

        // ── Execution Detection ──
        // Fires on every fill (entry, exit, partial)

        protected override void OnExecutionUpdate(Execution execution, string executionId, double price, int quantity, MarketPosition marketPosition, string orderId, DateTime time)
        {
            try
            {
                if (execution == null || execution.Order == null)
                    return;

                string orderAction = execution.Order.OrderAction.ToString().ToLower();
                bool isEntry = orderAction.Contains("buy") || orderAction.Contains("sell");
                bool isExit = orderAction.Contains("short") || orderAction.Contains("cover");

                string direction = "long";
                double entryPrice = price;
                int qty = quantity;

                // Determine direction from market position after fill
                if (marketPosition == MarketPosition.Long)
                    direction = "long";
                else if (marketPosition == MarketPosition.Short)
                    direction = "short";

                // Build the trade payload
                var tradeData = new
                {
                    event = isExit ? "exit" : "entry",
                    symbol = Instrument?.FullName ?? Instrument?.Name ?? "",
                    direction = direction,
                    quantity = (double)qty,
                    entry_price = isEntry ? price : _lastEntryPrice,
                    exit_price = isExit ? price : (double?)null,
                    stop_loss = (double?)null,  // Read from position if needed
                    take_profit = (double?)null,
                    fill_time = time.ToString("o"),
                    account = AccountName,
                    trade_id = orderId ?? executionId ?? "",
                    note = isExit ? "NT8 execution exit" : "NT8 execution entry",
                    capture_screenshot = AutoScreenshot,
                };

                // Track state
                if (isEntry)
                {
                    _lastEntryPrice = price;
                    _lastQuantity = qty;
                    _lastDirection = direction;
                    _hasOpenPosition = true;
                }
                else if (isExit)
                {
                    _hasOpenPosition = false;
                }

                // Send to journal
                string json = JsonConvert.SerializeObject(tradeData);
                SendToJournal(json);

                Log($"NT8 execution: {orderAction} {qty} {Instrument?.Name} @ {price}");
            }
            catch (Exception ex)
            {
                Log($"Error in OnExecutionUpdate: {ex.Message}");
            }
        }

        // ── Position Change Detection ──
        // Fires when position changes (SL moved, BE, partial)

        protected override void OnPositionUpdate(Cbi.Position position)
        {
            try
            {
                if (position == null) return;

                double avgPrice = position.AveragePrice;
                int qty = Math.Abs(position.Quantity);
                string direction = position.MarketPosition == MarketPosition.Long ? "long" : "short";

                // Detect modify events (SL/TP changes)
                if (position.StopLossPrice > 0)
                {
                    var modifyData = new
                    {
                        event = "modify",
                        symbol = Instrument?.FullName ?? "",
                        direction = direction,
                        quantity = (double)qty,
                        entry_price = avgPrice,
                        stop_loss = (double)position.StopLossPrice,
                        take_profit = (double?)null,
                        fill_time = DateTime.UtcNow.ToString("o"),
                        account = AccountName,
                        trade_id = "",
                        note = "SL update from NT8",
                        capture_screenshot = false,
                    };

                    string json = JsonConvert.SerializeObject(modifyData);
                    SendToJournal(json);

                    Log($"NT8 position update: SL={position.StopLossPrice} | Qty={qty}");
                }
            }
            catch (Exception ex)
            {
                Log($"Error in OnPositionUpdate: {ex.Message}");
            }
        }

        // ── HTTP Sender ──

        private async void SendToJournal(string json)
        {
            try
            {
                var content = new StringContent(json, Encoding.UTF8, "application/json");
                var response = await _http.PostAsync($"{JournalUrl}/api/nt8/trade", content);

                if (response.IsSuccessStatusCode)
                {
                    string responseBody = await response.Content.ReadAsStringAsync();
                    Log($"Journal OK: {responseBody}");

                    // Auto-screenshot on successful trade send
                    if (AutoScreenshot)
                    {
                        await Task.Delay(500); // Brief delay for chart to update
                        CaptureChartScreenshot();
                    }
                }
                else
                {
                    Log($"Journal error: {response.StatusCode}");
                }
            }
            catch (Exception ex)
            {
                Log($"Journal send failed: {ex.Message}");
            }
        }

        // ── Chart Screenshot Capture ──

        private async void CaptureChartScreenshot()
        {
            try
            {
                if (ChartControl == null) return;

                string screenshotDir = Path.Combine(
                    Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments),
                    "TradingJournalScreenshots"
                );
                Directory.CreateDirectory(screenshotDir);

                string filename = $"NT8_{Instrument?.Name}_{DateTime.Now:yyyyMMdd_HHmmss}.png";
                string filepath = Path.Combine(screenshotDir, filename);

                // Render chart to bitmap
                await ChartControl.Dispatcher.InvokeAsync(() =>
                {
                    double dpi = 96;
                    double width = ChartControl.ActualWidth;
                    double height = ChartControl.ActualHeight;

                    if (width <= 0 || height <= 0) return;

                    RenderTargetBitmap bitmap = new RenderTargetBitmap(
                        (int)width, (int)height, dpi, dpi, PixelFormats.Pbgra32
                    );

                    bitmap.Render(ChartControl);

                    PngBitmapEncoder encoder = new PngBitmapEncoder();
                    encoder.Frames.Add(BitmapFrame.Create(bitmap));

                    using (FileStream fs = new FileStream(filepath, FileMode.Create))
                    {
                        encoder.Save(fs);
                    }
                });

                Log($"Screenshot saved: {filepath}");

                // Send screenshot path to journal
                var ssData = new { trade_id = 0, event = "nt8_chart", file_path = filepath };
                string ssJson = JsonConvert.SerializeObject(ssData);
                var ssContent = new StringContent(ssJson, Encoding.UTF8, "application/json");
                await _http.PostAsync($"{JournalUrl}/api/nt8/screenshot", ssContent);
            }
            catch (Exception ex)
            {
                Log($"Screenshot failed: {ex.Message}");
            }
        }

        // ── Logging ──

        private void Log(string message)
        {
            if (DebugLogging)
            {
                NinjaTrader.Code.Output.Process(message, PrintTo.Log);
            }
        }
    }
}

#region NinjaScript generated code. Neither change nor remove.
// ... (auto-generated by NT8 compiler)
#endregion
