import { useState, useEffect } from 'react';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { TrendingUp, RefreshCw } from 'lucide-react';
import StatCards from '../components/StatCards';
import { fetchStatsSummary, fetchEquityCurve, fetchByMonth } from '../api/client';

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [equityCurve, setEquityCurve] = useState([]);
  const [byMonth, setByMonth] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
      setByMonth(monthRes.data || []);
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
      <div className="flex items-center justify-center py-24">
        <div className="flex flex-col items-center gap-3">
          <svg className="animate-spin h-8 w-8 text-accent" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-gray-500 text-sm">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <div className="text-4xl mb-4">⚠️</div>
        <h2 className="text-lg font-semibold text-gray-600 mb-2">Failed to load dashboard</h2>
        <p className="text-sm text-gray-400 mb-4">{error}</p>
        <button
          onClick={loadData}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-accent border border-accent/30 rounded-lg hover:bg-accent/5 transition-colors"
        >
          <RefreshCw size={16} />
          Retry
        </button>
      </div>
    );
  }

  if (!hasTrades) {
    return (
      <div>
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
        </div>
        <div className="text-center py-20 bg-white rounded-2xl shadow-sm border border-gray-100">
          <div className="text-6xl mb-4">📊</div>
          <h2 className="text-xl font-semibold text-gray-600 mb-2">No trades yet</h2>
          <p className="text-gray-400 max-w-md mx-auto">
            Import some trades to see your stats. Go to the Trades page to add your first trade, or use the Import page to upload a CSV.
          </p>
        </div>
      </div>
    );
  }

  // Prepare equity curve data for chart — backend returns {date, cumulative_pnl}[]
  const equityData = (Array.isArray(equityCurve) ? equityCurve : []).map(p => ({
    date: p.date,
    equity: p.cumulative_pnl,
  }));

  // Prepare month data — backend returns { "2026-01": {total_pnl, trade_count, win_count}, ... }
  const monthData = Object.entries(byMonth || {}).map(([month, data]) => ({
    month,
    pnl: data.total_pnl,
  })).sort((a, b) => a.month.localeCompare(b.month));

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Dashboard</h1>
          <p className="text-sm text-gray-400 mt-0.5">Trading performance overview</p>
        </div>
        <button
          onClick={loadData}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-500 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <RefreshCw size={14} />
          Refresh
        </button>
      </div>

      {/* Stat Cards */}
      <div className="mb-8">
        <StatCards summary={summary} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Equity Curve */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <TrendingUp size={16} className="text-accent" />
            Equity Curve
          </h3>
          {equityData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <AreaChart data={equityData}>
                <defs>
                  <linearGradient id="equityGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="date"
                  tick={{ fontSize: 11, fill: '#9ca3af' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: '#9ca3af' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e5e7eb' }}
                  tickFormatter={(v) => `$${v}`}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                    fontSize: '12px',
                  }}
                  formatter={(value) => [`$${Number(value).toFixed(2)}`, 'Equity']}
                />
                <Area
                  type="monotone"
                  dataKey="equity"
                  stroke="#22c55e"
                  strokeWidth={2}
                  fill="url(#equityGradient)"
                  dot={false}
                  activeDot={{ r: 4, stroke: '#22c55e', strokeWidth: 2, fill: '#fff' }}
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[280px] flex items-center justify-center text-gray-400 text-sm">
              No equity data available
            </div>
          )}
        </div>

        {/* PnL by Month */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
            <TrendingUp size={16} className="text-accent" />
            P&L by Month
          </h3>
          {monthData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={monthData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis
                  dataKey="month"
                  tick={{ fontSize: 11, fill: '#9ca3af' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e5e7eb' }}
                />
                <YAxis
                  tick={{ fontSize: 11, fill: '#9ca3af' }}
                  tickLine={false}
                  axisLine={{ stroke: '#e5e7eb' }}
                  tickFormatter={(v) => `$${v}`}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
                    fontSize: '12px',
                  }}
                  formatter={(value) => [`$${Number(value).toFixed(2)}`, 'PnL']}
                />
                <Bar
                  dataKey="pnl"
                  radius={[4, 4, 0, 0]}
                  fill="#3b82f6"
                  // Color based on value
                  shape={(props) => {
                    const { x, y, width, height, fill, payload } = props;
                    const color = payload.pnl >= 0 ? '#22c55e' : '#ef4444';
                    return <rect x={x} y={y} width={width} height={height} fill={color} rx={4} />;
                  }}
                />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[280px] flex items-center justify-center text-gray-400 text-sm">
              No monthly data available
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
