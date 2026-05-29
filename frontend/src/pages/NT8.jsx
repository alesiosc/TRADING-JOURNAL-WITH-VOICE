import { useState, useEffect } from 'react';
import { Server, Wifi, WifiOff, ExternalLink, Copy, CheckCircle, RefreshCw } from 'lucide-react';

export default function NT8() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);

  const checkStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/nt8/status');
      if (res.ok) setStatus(await res.json());
      else setStatus({ status: 'error' });
    } catch {
      setStatus({ status: 'error' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { checkStatus(); }, []);

  const journalUrl = window.location.origin.replace(/:\d+$/, ':8000');
  const isConnected = status?.status === 'ok';

  const copyUrl = () => {
    navigator.clipboard?.writeText(`${journalUrl}/api/nt8/trade`);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#0F172A] tracking-tight">NT8 Integration</h1>
        <p className="text-sm text-[#64748B] mt-1">NinjaTrader 8 trade connector</p>
      </div>

      {/* Connection status */}
      <div className="ghost-card">
        <div className="ghost-card-header">
          <h3 className="ghost-card-title"><Server size={16} className="text-[#3B82F6]" /> Connection</h3>
          {loading ? (
            <div className="flex items-center gap-2 text-sm text-[#64748B]">
              <RefreshCw size={14} className="animate-spin" /> Checking...
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <span className={`inline-flex items-center gap-1.5 pill ${isConnected ? 'pill-green' : 'pill-red'}`}>
                {isConnected ? <Wifi size={12} /> : <WifiOff size={12} />}
                {isConnected ? 'Connected' : 'Offline'}
              </span>
              <button onClick={checkStatus} className="btn-ghost-secondary !px-2 !py-1"><RefreshCw size={12} /></button>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
          <div className="space-y-2">
            <p className="text-[11px] font-semibold text-[#64748B] uppercase tracking-[0.06em]">Journal API URL</p>
            <div className="flex items-center gap-2">
              <code className="flex-1 px-3 py-2 bg-[#F8FAFC] border border-[#E9EDF2] rounded-lg text-xs font-mono text-[#0F172A]">
                {journalUrl}/api/nt8/trade
              </code>
              <button onClick={copyUrl} className="btn-ghost-secondary !px-2 !py-1.5" title="Copy URL">
                {copied ? <CheckCircle size={14} className="text-[#059669]" /> : <Copy size={14} />}
              </button>
            </div>
            <p className="text-xs text-[#94A3B8]">Use this in the NT8 indicator config</p>
          </div>
          <div className="space-y-2">
            <p className="text-[11px] font-semibold text-[#64748B] uppercase tracking-[0.06em]">Indicator Version</p>
            <p className="text-sm text-[#0F172A] font-medium">v{status?.version || '1.0.0'}</p>
            <p className="text-xs text-[#94A3B8]">TradeJournalConnector for NT8</p>
          </div>
        </div>
      </div>

      {/* Setup guide */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { step: '1', title: 'Copy Indicator', desc: 'Copy TradeJournalConnector.cs to your NT8 Indicators folder', detail: 'Documents\\NinjaTrader 8\\bin\\Custom\\Indicators\\' },
          { step: '2', title: 'Compile in NT8', desc: 'Open NinjaScript Editor (F11), right-click → Compile (F5)', detail: 'No compilation errors expected' },
          { step: '3', title: 'Add to Chart', desc: 'Right-click chart → Indicators → TradeJournalConnector', detail: `Set Journal URL to ${journalUrl}` },
        ].map((s) => (
          <div key={s.step} className="ghost-card">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-8 h-8 rounded-lg bg-[#EFF6FF] flex items-center justify-center text-sm font-bold text-[#2563EB]">
                {s.step}
              </div>
              <h4 className="text-sm font-semibold text-[#0F172A]">{s.title}</h4>
            </div>
            <p className="text-sm text-[#475569] mb-2">{s.desc}</p>
            <code className="text-[10px] text-[#64748B] bg-[#F8FAFC] block px-2 py-1.5 rounded border border-[#E9EDF2] font-mono">{s.detail}</code>
          </div>
        ))}
      </div>

      {/* Test card */}
      <div className="ghost-card">
        <div className="ghost-card-header">
          <h3 className="ghost-card-title">
            <ExternalLink size={16} className="text-[#3B82F6]" />
            Test the Connection
          </h3>
        </div>
        <p className="text-sm text-[#475569] mb-4">From your NT8 NinjaScript Editor, run this test in a new window (or use any indicator's OnBarUpdate):</p>
        <pre className="text-xs text-[#475569] bg-[#F8FAFC] border border-[#E9EDF2] rounded-xl p-4 overflow-x-auto font-mono leading-relaxed">{`HttpClient client = new HttpClient();
var data = new {
    event = "entry",
    symbol = "ES",
    direction = "long",
    quantity = 1,
    entry_price = 5245.50,
    account = "Sim101",
};
string json = JsonConvert.SerializeObject(data);
var content = new StringContent(json, Encoding.UTF8, "application/json");
var response = await client.PostAsync("${journalUrl}/api/nt8/trade", content);
Print("Journal: " + await response.Content.ReadAsStringAsync());`}</pre>
      </div>

      {/* Events reference */}
      <div className="ghost-card">
        <div className="ghost-card-header">
          <h3 className="ghost-card-title"><Server size={16} className="text-[#3B82F6]" /> Supported Events</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="ghost-table">
            <thead>
              <tr>
                <th className="px-4 py-2.5">Event</th>
                <th className="px-4 py-2.5">Trigger</th>
                <th className="px-4 py-2.5">Journal Action</th>
                <th className="px-4 py-2.5">Screenshot</th>
              </tr>
            </thead>
            <tbody>
              {[
                ['entry', 'Buy/Short entry fill', 'Creates trade + entry leg + journal note', '✓'],
                ['exit', 'Sell/Cover fill', 'Closes trade, auto-calculates P&L', '✓'],
                ['modify', 'SL move, BE, TP update', 'Updates trade, logs change as journal entry', '✓'],
                ['partial_close', 'Scale out', 'Adds reduce leg, adjusts quantity', '✓'],
              ].map(([ev, trigger, action, ss]) => (
                <tr key={ev}>
                  <td className="px-4 py-2.5"><code className="text-xs font-mono text-[#2563EB] bg-[#EFF6FF] px-1.5 py-0.5 rounded">{ev}</code></td>
                  <td className="px-4 py-2.5 text-xs text-[#475569]">{trigger}</td>
                  <td className="px-4 py-2.5 text-xs text-[#475569]">{action}</td>
                  <td className="px-4 py-2.5 text-center text-xs">{ss}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
