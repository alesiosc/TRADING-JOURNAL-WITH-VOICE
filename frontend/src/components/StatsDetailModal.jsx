import { useState, useMemo } from 'react';
import { X, TrendingUp, TrendingDown } from 'lucide-react';

const formatDate = (iso) => {
  if (!iso) return '\u2014';
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
};

/* ── Donut Chart ── */
function Donut({ pct, size = 72, stroke = 8, color = '#059669' }) {
  const r = (size - stroke) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (pct / 100) * circ;
  return (
    <svg width={size} height={size} className="rotate-[-90deg] shrink-0">
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="#F1F5F9" strokeWidth={stroke} />
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={color} strokeWidth={stroke} strokeDasharray={circ} strokeDashoffset={offset} strokeLinecap="round" />
    </svg>
  );
}

/* ── Horizontal Stacked Bar ── */
function StackedBar({ segments, height = 10 }) {
  const total = segments.reduce((s, seg) => s + seg.value, 0) || 1;
  return (
    <div className="flex rounded-full overflow-hidden h-[10px] w-full">
      {segments.map((seg, i) => (
        <div key={i} style={{ width: `${(seg.value / total) * 100}%`, backgroundColor: seg.color, minWidth: seg.value > 0 ? '4px' : '0' }} title={`${seg.label}: ${seg.value}`} />
      ))}
    </div>
  );
}

/* ── Streak Blocks ── */
function StreakBlocks({ wins = 0, losses = 0, max = 10 }) {
  const blocks = [];
  for (let i = 0; i < max; i++) {
    const isWin = i < wins;
    const isLoss = i >= wins && i < wins + losses;
    blocks.push(
      <div key={i} className={`w-5 h-5 rounded-sm ${isWin ? 'bg-[#059669]' : isLoss ? 'bg-[#DC2626]' : 'bg-[#F1F5F9]'}`} />
    );
  }
  return <div className="flex gap-1 flex-wrap">{blocks}</div>;
}

/* ── Mini Equity Bar ── */
function MiniEquityBar({ trades }) {
  if (!trades || trades.length === 0) return null;
  const sorted = [...trades].sort((a, b) => new Date(a.exit_time || a.entry_time) - new Date(b.exit_time || b.entry_time));
  let running = 0;
  let maxVal = 0;
  const points = sorted.map((t) => { running += t.pnl || 0; maxVal = Math.max(maxVal, Math.abs(running)); return running; });
  const total = points[points.length - 1] || 0;
  const h = 48;
  const w = 160;
  const min = Math.min(...points, 0);
  const range = Math.max(maxVal, Math.abs(min)) * 2 || 1;
  const zeroY = h - (0 - min) / range * h;
  const stepX = points.length > 1 ? w / (points.length - 1) : w;

  const pathD = points.map((p, i) => {
    const x = i * stepX;
    const y = h - (p - min) / range * h;
    return `${i === 0 ? 'M' : 'L'}${x},${y}`;
  }).join(' ');

  const fillD = pathD + ` L${(points.length - 1) * stepX},${zeroY} L0,${zeroY} Z`;

  return (
    <svg width={w} height={h} className="shrink-0">
      <line x1={0} y1={zeroY} x2={w} y2={zeroY} stroke="#E2E6EC" strokeWidth={1} />
      <path d={fillD} fill={total >= 0 ? 'rgba(5,150,105,0.12)' : 'rgba(220,38,38,0.12)'} />
      <path d={pathD} fill="none" stroke={total >= 0 ? '#059669' : '#DC2626'} strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" />
      <circle cx={w} cy={h - (total - min) / range * h} r={3} fill={total >= 0 ? '#059669' : '#DC2626'} />
    </svg>
  );
}

/* ── Comparison Bar ── */
function ComparisonBar({ label1, val1, label2, val2, color1 = '#059669', color2 = '#DC2626' }) {
  const max = Math.max(val1, val2, 1);
  return (
    <div className="space-y-1.5 w-full">
      <div className="flex items-center justify-between text-xs">
        <span className="text-[#64748B]">{label1}</span>
        <span className="font-semibold text-[#059669]">${val1.toLocaleString()}</span>
      </div>
      <div className="h-2 bg-[#F1F5F9] rounded-full overflow-hidden">
        <div className="h-full rounded-full bg-[#059669] transition-all" style={{ width: `${(val1 / max) * 100}%` }} />
      </div>
      <div className="flex items-center justify-between text-xs mt-2">
        <span className="text-[#64748B]">{label2}</span>
        <span className="font-semibold text-[#DC2626]">${val2.toLocaleString()}</span>
      </div>
      <div className="h-2 bg-[#F1F5F9] rounded-full overflow-hidden">
        <div className="h-full rounded-full bg-[#DC2626] transition-all" style={{ width: `${(val2 / max) * 100}%` }} />
      </div>
    </div>
  );
}

/* ── Module Definitions ── */

const MODULES = {
  'Total P&L': {
    title: 'Profit & Loss History',
    icon: TrendingUp,
    graphic: (s, trades) => (
      <div className="flex items-center gap-6">
        <MiniEquityBar trades={trades} />
        <div className="space-y-1">
          <div className="flex items-center gap-2 text-sm"><div className="w-3 h-3 rounded bg-[#059669]" /> <span className="text-[#64748B]">Gross Profit: <strong className="text-[#059669]">${(s?.gross_profit || 0).toLocaleString()}</strong></span></div>
          <div className="flex items-center gap-2 text-sm"><div className="w-3 h-3 rounded bg-[#DC2626]" /> <span className="text-[#64748B]">Gross Loss: <strong className="text-[#DC2626]">${(s?.gross_loss || 0).toLocaleString()}</strong></span></div>
          <div className="flex items-center gap-2 text-sm"><div className="w-3 h-3 rounded bg-[#3B82F6]" /> <span className="text-[#64748B]">Net: <strong className={s?.total_pnl >= 0 ? 'text-[#059669]' : 'text-[#DC2626]'}>${(s?.total_pnl || 0).toLocaleString()}</strong></span></div>
        </div>
      </div>
    ),
    sortTrades: (trades) => [...trades].sort((a, b) => (b.pnl || 0) - (a.pnl || 0)),
    columns: ['#', 'Trade', 'Direction', 'P&L', 'Running Total', 'Date'],
    renderRow: (trade, idx) => {
      const pnl = trade.pnl || 0;
      return (
        <tr key={trade.id} className="hover:bg-[#F8FAFC] transition-colors cursor-pointer">
          <td className="px-4 py-3 text-xs text-[#94A3B8] w-8">{idx + 1}</td>
          <td className="px-4 py-3 text-sm font-medium text-[#0F172A]">{trade.instrument?.symbol || trade.symbol}</td>
          <td className="px-4 py-3">
            <span className={`inline-flex items-center gap-1 text-xs font-medium ${trade.direction === 'long' ? 'text-[#059669]' : 'text-[#DC2626]'}`}>
              {trade.direction === 'long' ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {trade.direction}
            </span>
          </td>
          <td className={`px-4 py-3 text-sm font-semibold ${pnl > 0 ? 'text-[#059669]' : pnl < 0 ? 'text-[#DC2626]' : 'text-[#64748B]'}`}>
            {pnl > 0 ? '+' : ''}${pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </td>
          <td className={`px-4 py-3 text-sm font-mono ${pnl > 0 ? 'text-[#059669]' : pnl < 0 ? 'text-[#DC2626]' : 'text-[#64748B]'}`}>
            ${pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </td>
          <td className="px-4 py-3 text-xs text-[#64748B]">{formatDate(trade.exit_time || trade.entry_time)}</td>
        </tr>
      );
    },
  },
  'Win Rate': {
    title: 'Win / Loss Breakdown',
    icon: TrendingUp,
    graphic: (s) => {
      const wins = s?.trade_count?.winning || 0;
      const losses = s?.trade_count?.losing || 0;
      const total = wins + losses || 1;
      const pct = (wins / total) * 100;
      return (
        <div className="flex items-center gap-8">
          <div className="relative flex items-center justify-center" style={{ width: 72, height: 72 }}>
            <Donut pct={pct} size={72} stroke={8} color="#059669" />
            <span className="absolute text-lg font-bold text-[#0F172A]">{wins}</span>
          </div>
          <div className="space-y-2 flex-1">
            <StackedBar segments={[
              { label: 'Wins', value: wins, color: '#059669' },
              { label: 'Losses', value: losses, color: '#DC2626' },
            ]} />
            <div className="flex justify-between text-xs">
              <span className="text-[#059669] font-semibold">{wins} Wins ({pct.toFixed(0)}%)</span>
              <span className="text-[#DC2626] font-semibold">{losses} Losses ({(100 - pct).toFixed(0)}%)</span>
            </div>
          </div>
        </div>
      );
    },
    sortTrades: (trades) => [...trades].sort((a, b) => new Date(b.exit_time || b.entry_time) - new Date(a.exit_time || a.entry_time)),
    columns: ['#', 'Trade', 'Direction', 'Entry', 'Exit', 'P&L', 'Outcome', 'Date'],
    renderRow: (trade, idx) => {
      const pnl = trade.pnl || 0;
      const outcome = pnl > 0 ? 'Win' : pnl < 0 ? 'Loss' : 'BE';
      const outcomeColor = pnl > 0 ? 'pill-green' : pnl < 0 ? 'pill-red' : 'pill-gray';
      return (
        <tr key={trade.id} className="hover:bg-[#F8FAFC] transition-colors cursor-pointer">
          <td className="px-4 py-3 text-xs text-[#94A3B8] w-8">{idx + 1}</td>
          <td className="px-4 py-3 text-sm font-medium text-[#0F172A]">{trade.instrument?.symbol || trade.symbol}</td>
          <td className="px-4 py-3">
            <span className={`inline-flex items-center gap-1 text-xs font-medium ${trade.direction === 'long' ? 'text-[#059669]' : 'text-[#DC2626]'}`}>
              {trade.direction === 'long' ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {trade.direction}
            </span>
          </td>
          <td className="px-4 py-3 text-xs font-mono text-[#475569]">${Number(trade.entry_price)?.toFixed(2)}</td>
          <td className="px-4 py-3 text-xs font-mono text-[#475569]">{trade.exit_price != null ? `$${Number(trade.exit_price).toFixed(2)}` : '\u2014'}</td>
          <td className={`px-4 py-3 text-sm font-semibold ${pnl > 0 ? 'text-[#059669]' : pnl < 0 ? 'text-[#DC2626]' : 'text-[#64748B]'}`}>
            {pnl > 0 ? '+' : ''}${pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </td>
          <td className="px-4 py-3"><span className={outcomeColor}>{outcome}</span></td>
          <td className="px-4 py-3 text-xs text-[#64748B]">{formatDate(trade.exit_time || trade.entry_time)}</td>
        </tr>
      );
    },
  },
  'Profit Factor': {
    title: 'Profit Factor Detail',
    icon: TrendingUp,
    graphic: (s) => (
      <ComparisonBar
        label1="Gross Profit"
        val1={s?.gross_profit || 0}
        label2="Gross Loss"
        val2={s?.gross_loss || 0}
      />
    ),
    sortTrades: (trades) => [...trades].sort((a, b) => Math.abs(b.pnl || 0) - Math.abs(a.pnl || 0)),
    columns: ['#', 'Trade', 'Direction', 'P&L', 'Type', 'Date'],
    renderRow: (trade, idx) => {
      const pnl = trade.pnl || 0;
      return (
        <tr key={trade.id} className="hover:bg-[#F8FAFC] transition-colors cursor-pointer">
          <td className="px-4 py-3 text-xs text-[#94A3B8] w-8">{idx + 1}</td>
          <td className="px-4 py-3 text-sm font-medium text-[#0F172A]">{trade.instrument?.symbol || trade.symbol}</td>
          <td className="px-4 py-3">
            <span className={`inline-flex items-center gap-1 text-xs font-medium ${trade.direction === 'long' ? 'text-[#059669]' : 'text-[#DC2626]'}`}>
              {trade.direction === 'long' ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {trade.direction}
            </span>
          </td>
          <td className={`px-4 py-3 text-sm font-semibold ${pnl > 0 ? 'text-[#059669]' : pnl < 0 ? 'text-[#DC2626]' : 'text-[#64748B]'}`}>
            {pnl > 0 ? '+' : ''}${pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </td>
          <td className="px-4 py-3">
            <span className={pnl > 0 ? 'pill-green' : pnl < 0 ? 'pill-red' : 'pill-gray'}>
              {pnl > 0 ? 'Winner' : pnl < 0 ? 'Loser' : 'Breakeven'}
            </span>
          </td>
          <td className="px-4 py-3 text-xs text-[#64748B]">{formatDate(trade.exit_time || trade.entry_time)}</td>
        </tr>
      );
    },
  },
  'Trades': {
    title: 'Trade Activity',
    icon: TrendingUp,
    graphic: (s) => {
      const wins = s?.trade_count?.winning || 0;
      const losses = s?.trade_count?.losing || 0;
      const be = s?.trade_count?.breakeven || 0;
      const total = wins + losses + be || 1;
      return (
        <div className="flex items-center gap-6">
          <div className="relative flex items-center justify-center" style={{ width: 72, height: 72 }}>
            <Donut pct={(wins / total) * 100} size={72} stroke={8} color="#059669" />
            <span className="absolute text-lg font-bold text-[#0F172A]">{total}</span>
          </div>
          <div className="space-y-2 flex-1">
            <StackedBar segments={[
              { label: 'Wins', value: wins, color: '#059669' },
              { label: 'Losses', value: losses, color: '#DC2626' },
              { label: 'BE', value: be, color: '#94A3B8' },
            ]} />
            <div className="flex justify-between text-xs">
              <span className="text-[#059669] font-semibold">{wins} Wins</span>
              <span className="text-[#DC2626] font-semibold">{losses} Losses</span>
              <span className="text-[#64748B] font-semibold">{be} BE</span>
            </div>
          </div>
        </div>
      );
    },
    sortTrades: (trades) => [...trades].sort((a, b) => new Date(b.entry_time || 0) - new Date(a.entry_time || 0)),
    columns: ['#', 'Trade', 'Status', 'Direction', 'P&L', 'Date'],
    renderRow: (trade, idx) => {
      const pnl = trade.pnl || 0;
      return (
        <tr key={trade.id} className="hover:bg-[#F8FAFC] transition-colors cursor-pointer">
          <td className="px-4 py-3 text-xs text-[#94A3B8] w-8">{idx + 1}</td>
          <td className="px-4 py-3 text-sm font-medium text-[#0F172A]">{trade.instrument?.symbol || trade.symbol}</td>
          <td className="px-4 py-3">
            <span className={`pill ${trade.status === 'closed' ? 'pill-gray' : 'pill-orange'}`}>
              <span className={`status-dot ${trade.status === 'closed' ? 'status-dot-closed' : 'status-dot-open'}`} />
              {trade.status}
            </span>
          </td>
          <td className="px-4 py-3">
            <span className={`inline-flex items-center gap-1 text-xs font-medium ${trade.direction === 'long' ? 'text-[#059669]' : 'text-[#DC2626]'}`}>
              {trade.direction === 'long' ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
              {trade.direction}
            </span>
          </td>
          <td className={`px-4 py-3 text-sm font-semibold ${pnl > 0 ? 'text-[#059669]' : pnl < 0 ? 'text-[#DC2626]' : 'text-[#64748B]'}`}>
            {pnl > 0 ? '+' : ''}${pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </td>
          <td className="px-4 py-3 text-xs text-[#64748B]">{formatDate(trade.entry_time)}</td>
        </tr>
      );
    },
  },
  'Avg Win': {
    title: 'Winning Trades',
    icon: TrendingUp,
    graphic: (s) => {
      const wins = s?.trade_count?.winning || 0;
      const avg = s?.avg_win || 0;
      const best = s?.best_trade?.pnl || 0;
      return (
        <div className="flex items-center gap-6">
          <div className="relative flex items-center justify-center" style={{ width: 72, height: 72 }}>
            <Donut pct={100} size={72} stroke={8} color="#059669" />
            <span className="absolute text-lg font-bold text-[#059669]">{wins}</span>
          </div>
          <div className="space-y-2 flex-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-[#64748B]">Average Win</span>
              <span className="text-lg font-bold text-[#059669]">${avg.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
            </div>
            <div className="h-2 bg-[#F1F5F9] rounded-full overflow-hidden">
              <div className="h-full rounded-full bg-[#059669]" style={{ width: `${(avg / Math.max(best, 1)) * 100}%` }} />
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[#64748B]">vs Best: ${best.toLocaleString()}</span>
              <span className="text-[#64748B]">{wins} winners</span>
            </div>
          </div>
        </div>
      );
    },
    sortTrades: (trades) => [...trades].filter(t => (t.pnl || 0) > 0).sort((a, b) => (b.pnl || 0) - (a.pnl || 0)),
    columns: ['#', 'Trade', 'Direction', 'Volume', 'Entry', 'Exit', 'P&L', 'R', 'Date'],
    renderRow: (trade, idx) => {
      const pnl = trade.pnl || 0;
      return (
        <tr key={trade.id} className="hover:bg-[#F8FAFC] transition-colors cursor-pointer">
          <td className="px-4 py-3 text-xs text-[#94A3B8] w-8">{idx + 1}</td>
          <td className="px-4 py-3 text-sm font-medium text-[#0F172A]">{trade.instrument?.symbol || trade.symbol}</td>
          <td className="px-4 py-3">
            <span className="inline-flex items-center gap-1 text-xs font-medium text-[#059669]">
              <TrendingUp size={12} /> {trade.direction}
            </span>
          </td>
          <td className="px-4 py-3 text-xs text-[#475569]">{trade.volume || trade.quantity || '\u2014'}</td>
          <td className="px-4 py-3 text-xs font-mono text-[#475569]">${Number(trade.entry_price)?.toFixed(2)}</td>
          <td className="px-4 py-3 text-xs font-mono text-[#475569]">{trade.exit_price != null ? `$${Number(trade.exit_price).toFixed(2)}` : '\u2014'}</td>
          <td className="px-4 py-3 text-sm font-semibold text-[#059669]">+${pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
          <td className="px-4 py-3 text-xs text-[#64748B]">{trade.pnl_pct != null ? `${trade.pnl_pct.toFixed(1)}%` : '\u2014'}</td>
          <td className="px-4 py-3 text-xs text-[#64748B]">{formatDate(trade.exit_time || trade.entry_time)}</td>
        </tr>
      );
    },
  },
  'Avg Loss': {
    title: 'Losing Trades',
    icon: TrendingDown,
    graphic: (s) => {
      const losses = s?.trade_count?.losing || 0;
      const avg = Math.abs(s?.avg_loss || 0);
      const worst = Math.abs(s?.worst_trade?.pnl || 0);
      return (
        <div className="flex items-center gap-6">
          <div className="relative flex items-center justify-center" style={{ width: 72, height: 72 }}>
            <Donut pct={100} size={72} stroke={8} color="#DC2626" />
            <span className="absolute text-lg font-bold text-[#DC2626]">{losses}</span>
          </div>
          <div className="space-y-2 flex-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-[#64748B]">Average Loss</span>
              <span className="text-lg font-bold text-[#DC2626]">${avg.toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
            </div>
            <div className="h-2 bg-[#F1F5F9] rounded-full overflow-hidden">
              <div className="h-full rounded-full bg-[#DC2626]" style={{ width: `${(avg / Math.max(worst, 1)) * 100}%` }} />
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[#64748B]">vs Worst: ${worst.toLocaleString()}</span>
              <span className="text-[#64748B]">{losses} losers</span>
            </div>
          </div>
        </div>
      );
    },
    sortTrades: (trades) => [...trades].filter(t => (t.pnl || 0) < 0).sort((a, b) => (a.pnl || 0) - (b.pnl || 0)),
    columns: ['#', 'Trade', 'Direction', 'Volume', 'Entry', 'Exit', 'P&L', 'R', 'Date'],
    renderRow: (trade, idx) => {
      const pnl = trade.pnl || 0;
      return (
        <tr key={trade.id} className="hover:bg-[#F8FAFC] transition-colors cursor-pointer">
          <td className="px-4 py-3 text-xs text-[#94A3B8] w-8">{idx + 1}</td>
          <td className="px-4 py-3 text-sm font-medium text-[#0F172A]">{trade.instrument?.symbol || trade.symbol}</td>
          <td className="px-4 py-3">
            <span className="inline-flex items-center gap-1 text-xs font-medium text-[#DC2626]">
              <TrendingDown size={12} /> {trade.direction}
            </span>
          </td>
          <td className="px-4 py-3 text-xs text-[#475569]">{trade.volume || trade.quantity || '\u2014'}</td>
          <td className="px-4 py-3 text-xs font-mono text-[#475569]">${Number(trade.entry_price)?.toFixed(2)}</td>
          <td className="px-4 py-3 text-xs font-mono text-[#475569]">{trade.exit_price != null ? `$${Number(trade.exit_price).toFixed(2)}` : '\u2014'}</td>
          <td className="px-4 py-3 text-sm font-semibold text-[#DC2626]">-${Math.abs(pnl).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
          <td className="px-4 py-3 text-xs text-[#64748B]">{trade.pnl_pct != null ? `${trade.pnl_pct.toFixed(1)}%` : '\u2014'}</td>
          <td className="px-4 py-3 text-xs text-[#64748B]">{formatDate(trade.exit_time || trade.entry_time)}</td>
        </tr>
      );
    },
  },
  'W / L': {
    title: 'Win / Loss Streaks',
    icon: TrendingUp,
    graphic: (s) => {
      const bestStreak = s?.max_consecutive_wins || 0;
      const worstStreak = s?.max_consecutive_losses || 0;
      return (
        <div className="flex items-center gap-8">
          <div className="space-y-2 text-center">
            <p className="text-xs text-[#64748B] font-medium">Best Streak</p>
            <div className="flex items-center gap-1.5 justify-center">
              <span className="text-2xl font-bold text-[#059669]">{bestStreak}</span>
              <TrendingUp size={20} className="text-[#059669]" />
            </div>
            <StreakBlocks wins={bestStreak} losses={0} max={Math.max(bestStreak, worstStreak, 5)} />
          </div>
          <div className="text-[#E2E6EC] text-2xl font-light">|</div>
          <div className="space-y-2 text-center">
            <p className="text-xs text-[#64748B] font-medium">Worst Streak</p>
            <div className="flex items-center gap-1.5 justify-center">
              <span className="text-2xl font-bold text-[#DC2626]">{worstStreak}</span>
              <TrendingDown size={20} className="text-[#DC2626]" />
            </div>
            <StreakBlocks wins={0} losses={worstStreak} max={Math.max(bestStreak, worstStreak, 5)} />
          </div>
          <div className="text-[#E2E6EC] text-2xl font-light">|</div>
          <div className="space-y-2 text-center">
            <p className="text-xs text-[#64748B] font-medium">Win Rate</p>
            <p className="text-2xl font-bold text-[#0F172A]">{(s?.win_rate || 0).toFixed(0)}%</p>
            <p className="text-xs text-[#64748B]">{s?.trade_count?.winning || 0}W / {s?.trade_count?.losing || 0}L</p>
          </div>
        </div>
      );
    },
    sortTrades: (trades) => [...trades].sort((a, b) => new Date(b.exit_time || b.entry_time) - new Date(a.exit_time || a.entry_time)),
    columns: ['#', 'Trade', 'P&L', 'Streak', 'Date'],
    renderRow: (trade, idx, _rt, streakTracker) => {
      const pnl = trade.pnl || 0;
      const allSorted = [...(streakTracker?._allTrades || [])].sort(
        (a, b) => new Date(a.exit_time || a.entry_time) - new Date(b.exit_time || b.entry_time)
      );
      let winStreak = 0, lossStreak = 0;
      const streaks = {};
      allSorted.forEach((t) => {
        const tp = t.pnl || 0;
        if (tp > 0) { winStreak++; lossStreak = 0; }
        else if (tp < 0) { lossStreak++; winStreak = 0; }
        else { winStreak = 0; lossStreak = 0; }
        streaks[t.id] = { count: tp > 0 ? winStreak : tp < 0 ? lossStreak : 0, type: tp > 0 ? 'win' : tp < 0 ? 'loss' : 'be' };
      });
      const streak = streaks[trade.id];
      return (
        <tr key={trade.id} className="hover:bg-[#F8FAFC] transition-colors cursor-pointer">
          <td className="px-4 py-3 text-xs text-[#94A3B8] w-8">{idx + 1}</td>
          <td className="px-4 py-3 text-sm font-medium text-[#0F172A]">{trade.instrument?.symbol || trade.symbol}</td>
          <td className={`px-4 py-3 text-sm font-semibold ${pnl > 0 ? 'text-[#059669]' : pnl < 0 ? 'text-[#DC2626]' : 'text-[#64748B]'}`}>
            {pnl > 0 ? '+' : ''}${pnl.toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </td>
          <td className="px-4 py-3">
            {streak && streak.count > 0 ? (
              <span className={streak.type === 'win' ? 'pill-green' : streak.type === 'loss' ? 'pill-red' : 'pill-gray'}>
                {streak.count}x {streak.type === 'win' ? '\u25B2' : '\u25BC'}
              </span>
            ) : <span className="pill-gray">\u2014</span>}
          </td>
          <td className="px-4 py-3 text-xs text-[#64748B]">{formatDate(trade.exit_time || trade.entry_time)}</td>
        </tr>
      );
    },
  },
};

export default function StatsDetailModal({ moduleKey, summary, trades, onClose }) {
  const module = MODULES[moduleKey];
  if (!module) return null;

  const sortedTrades = useMemo(() => module.sortTrades(trades || []), [moduleKey, trades]);

  const Icon = module.icon || TrendingUp;

  return (
    <div className="fixed inset-0 z-50 modal-overlay flex items-center justify-center p-4" onClick={onClose}>
      <div className="modal-content bg-white rounded-2xl border border-[#E9EDF2] w-full max-w-4xl max-h-[90vh] flex flex-col" style={{ boxShadow: '0 25px 60px 0 rgba(15, 23, 42, 0.12), 0 0 0 1px rgba(0, 0, 0, 0.03)' }} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-start justify-between px-6 py-5 border-b border-[#E9EDF2]">
          <div className="flex items-start gap-4 flex-1">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#2563EB] to-[#3B82F6] flex items-center justify-center shadow-sm shrink-0 mt-0.5">
              <Icon size={20} className="text-white" />
            </div>
            <div className="flex-1">
              <h2 className="text-lg font-bold text-[#0F172A]">{module.title}</h2>
              <p className="text-sm text-[#64748B] mt-0.5">{module.subtitle}</p>
              {summary && (
                <p className="text-xs text-[#94A3B8] mt-1">{module.description?.(summary)}</p>
              )}
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-[#94A3B8] hover:text-[#475569] rounded-lg hover:bg-[#F1F5F9] transition-colors">
            <X size={20} />
          </button>
        </div>

        {/* Graphical Profile */}
        {module.graphic && (
          <div className="px-6 py-5 bg-[#F8FAFC] border-b border-[#E9EDF2]">
            {module.graphic(summary, trades)}
          </div>
        )}

        {/* Table */}
        <div className="flex-1 overflow-y-auto p-2">
          <table className="ghost-table">
            <thead className="sticky top-0 bg-white">
              <tr>
                {module.columns.map((col) => (
                  <th key={col} className="px-4 py-3 text-[11px] font-semibold text-[#64748B] uppercase tracking-[0.06em] text-left">{col}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedTrades.length === 0 ? (
                <tr><td colSpan={module.columns.length} className="text-center py-12 text-sm text-[#94A3B8]">No trades match this filter.</td></tr>
              ) : (
                sortedTrades.map((trade, idx) => {
                  const streakTracker = { _allTrades: trades };
                  return module.renderRow(trade, idx, 0, streakTracker);
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-[#E9EDF2] text-xs text-[#94A3B8] text-center">
          {sortedTrades.length} trade{sortedTrades.length !== 1 ? 's' : ''} displayed
        </div>
      </div>
    </div>
  );
}
