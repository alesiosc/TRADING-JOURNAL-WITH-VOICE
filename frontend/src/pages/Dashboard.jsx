import { useState, useEffect } from 'react';
import {
  AreaChart, Area, BarChart, Bar, Cell, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { TrendingUp, RefreshCw } from 'lucide-react';
import StatCards from '../components/StatCards';
import StatsDetailModal from '../components/StatsDetailModal';
import { fetchStatsSummary, fetchEquityCurve, fetchByMonth, fetchTrades } from '../api/client';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white border border-[#E9EDF2] rounded-xl px-3.5 py-2.5 text-xs shadow-lg" style={{ boxShadow: '0 4px 16px 0 rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.02)' }}>
        <p className="font-semibold text-[#0F172A] text-[13px] mb-1">{label}</p>
        {payload.map((p, i) => (
          <p key={i} className={p.value > 0 ? 'text-[#059669] font-medium' : 'text-[#DC2626] font-medium'}>
            {p.name}: ${Number(p.value).toLocaleString(undefined, { minimumFractionDigits: 2 })}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [equityCurve, setEquityCurve] = useState([]);
  const [byMonth, setByMonth] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [allTrades, setAllTrades] = useState([]);
  const [detailModule, setDetailModule] = useState(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [sumRes, equityRes, monthRes] = await Promise.all([
        fetchStatsSummary(),
        fetchEquityCurve(),
        fetchByMonth(),
      ]);
      if (sumRes.error) throw new Error(sumRes.error);
      if (equityRes.error) throw new Error(equityRes.error);
      if (monthRes.error) throw new Error(monthRes.error);

      setSummary(sumRes.data);
      setEquityCurve(equityRes.data || []);

      // Fetch all trades for detail modals
      const tradeRes = await fetchTrades({ limit: 500 });
      if (!tradeRes.error) setAllTrades(tradeRes.data || []);

      // Transform by-month dict into array for Recharts
      const rawByMonth = monthRes.data || {};
      const transformed = Object.entries(rawByMonth).map(([month, data]) => ({
        month,
        pnl: data.total_pnl || 0,
      }));
      setByMonth(transformed);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const hasTrades = summary?.trade_count?.total > 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-32">
        <div className="flex flex-col items-center gap-4">
          <svg className="animate-spin h-8 w-8 text-[#3B82F6]" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-sm text-[#94A3B8]">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-32">
        <div className="text-4xl mb-4">\u26A0\uFE0F</div>
        <h2 className="text-lg font-semibold text-[#64748B] mb-1">Failed to load</h2>
        <p className="text-sm text-[#94A3B8] mb-5">{error}</p>
        <button onClick={loadData} className="btn-primary">Retry</button>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[#0F172A] tracking-tight">Dashboard</h1>
          <p className="text-sm text-[#64748B] mt-1">Trading performance overview</p>
        </div>
        <button onClick={loadData} className="btn-ghost-secondary">
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {/* Stat cards */}
      <StatCards summary={summary} onCardClick={setDetailModule} />

      {!hasTrades ? (
        <div className="ghost-card text-center py-16">
          <TrendingUp size={40} className="mx-auto mb-4 text-[#CBD5E1]" />
          <h3 className="text-lg font-semibold text-[#64748B] mb-1">No trades yet</h3>
          <p className="text-sm text-[#94A3B8]">Import a CSV or add your first trade to see stats.</p>
        </div>
      ) : (
        <>
          {/* Equity Curve */}
          <div className="chart-container">
            <div className="ghost-card-header">
              <h3 className="ghost-card-title">
                <TrendingUp size={16} className="text-[#3B82F6]" />
                Equity Curve
              </h3>
              <span className="pill-gray">{equityCurve.length} trades</span>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={equityCurve} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                  <defs>
                    <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.15} />
                      <stop offset="100%" stopColor="#3B82F6" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="4 4" stroke="#F1F5F9" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#94A3B8' }} axisLine={{ stroke: '#E9EDF2' }} tickLine={false} tickFormatter={(v) => { const d = new Date(v); return `${d.getMonth()+1}/${d.getDate()}`; }} />
                  <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${v}`} width={60} />
                  <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#E9EDF2', strokeDasharray: '4 4' }} />
                  <Area type="monotone" dataKey="cumulative_pnl" stroke="#3B82F6" strokeWidth={2.5} fill="url(#equityGradient)" dot={false} activeDot={{ r: 5, fill: '#3B82F6', stroke: '#fff', strokeWidth: 2 }} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Monthly P&L */}
          <div className="chart-container">
            <div className="ghost-card-header">
              <h3 className="ghost-card-title">
                <TrendingUp size={16} className="text-[#3B82F6]" />
                P&amp;L by Month
              </h3>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={byMonth} margin={{ top: 8, right: 12, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="4 4" stroke="#F1F5F9" vertical={false} />
                  <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#94A3B8' }} axisLine={{ stroke: '#E9EDF2' }} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: '#94A3B8' }} axisLine={false} tickLine={false} tickFormatter={(v) => `$${v}`} width={60} />
                  <Tooltip content={<CustomTooltip />} cursor={{ fill: '#F8FAFC' }} />
                  <Bar dataKey="pnl" radius={[6, 6, 0, 0]} maxBarSize={48}>
                    {byMonth.map((entry, idx) => (
                      <Cell key={idx} fill={entry.pnl >= 0 ? '#059669' : '#DC2626'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}

      {/* Stats Detail Modal */}
      {detailModule && (
        <StatsDetailModal
          moduleKey={detailModule}
          summary={summary}
          trades={allTrades}
          onClose={() => setDetailModule(null)}
        />
      )}
    </div>
  );
}
