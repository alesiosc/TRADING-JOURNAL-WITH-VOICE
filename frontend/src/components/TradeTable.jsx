import { useState, useMemo } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown, Trash2, ChevronRight } from 'lucide-react';

export default function TradeTable({ trades, onSelect, onDelete }) {
  const [sortField, setSortField] = useState('entry_time');
  const [sortDir, setSortDir] = useState('desc');

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDir('asc');
    }
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) return <ArrowUpDown size={13} className="text-gray-400 ml-1" />;
    return sortDir === 'asc'
      ? <ArrowUp size={13} className="text-accent ml-1" />
      : <ArrowDown size={13} className="text-accent ml-1" />;
  };

  const sortedTrades = useMemo(() => {
    if (!trades || trades.length === 0) return [];
    return [...trades].sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];

      // Handle nested fields
      if (sortField === 'entry_time' || sortField === 'exit_time') {
        aVal = a[sortField] || '';
        bVal = b[sortField] || '';
      }

      if (aVal == null) return 1;
      if (bVal == null) return -1;

      if (typeof aVal === 'number') {
        return sortDir === 'asc' ? aVal - bVal : bVal - aVal;
      }
      // String comparison
      const cmp = String(aVal).localeCompare(String(bVal));
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [trades, sortField, sortDir]);

  const formatDateTime = (iso) => {
    if (!iso) return '—';
    const d = new Date(iso);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) +
      ' ' + d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
  };

  const formatDuration = (entryIso, exitIso) => {
    if (!entryIso || !exitIso) return '—';
    const ms = new Date(exitIso) - new Date(entryIso);
    if (ms < 0) return '—';
    const hours = Math.floor(ms / 3600000);
    const minutes = Math.floor((ms % 3600000) / 60000);
    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `${days}d ${hours % 24}h`;
    }
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  if (!trades || trades.length === 0) {
    return (
      <div className="text-center py-16 text-gray-400">
        <div className="text-5xl mb-4">📋</div>
        <p className="text-lg font-medium text-gray-500">No trades yet</p>
        <p className="text-sm mt-1">Click "New Trade" to add your first trade, or import from CSV.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto bg-white rounded-xl shadow-sm border border-gray-100">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-gray-100 bg-gray-50/80">
            {[
              { key: 'entry_time', label: 'Date / Time' },
              { key: 'instrument', label: 'Instrument' },
              { key: 'direction', label: 'Dir.' },
              { key: 'volume', label: 'Volume' },
              { key: 'entry_price', label: 'Entry' },
              { key: 'exit_price', label: 'Exit' },
              { key: 'pnl', label: 'PnL' },
              { key: 'duration', label: 'Duration' },
              { key: 'strategy_tag', label: 'Tags' },
            ].map((col) => (
              <th
                key={col.key}
                className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider cursor-pointer select-none hover:text-gray-700 whitespace-nowrap"
                onClick={() => handleSort(col.key)}
              >
                <span className="inline-flex items-center">
                  {col.label}
                  <SortIcon field={col.key} />
                </span>
              </th>
            ))}
            <th className="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">
              Actions
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedTrades.map((trade, idx) => {
            const isLong = trade.direction === 'long';
            const pnl = trade.pnl;
            const pnlNum = pnl != null ? Number(pnl) : null;

            return (
              <tr
                key={trade.id || idx}
                className={`border-b border-gray-50 hover:bg-blue-50/40 cursor-pointer transition-colors ${
                  idx % 2 === 1 ? 'bg-gray-50/30' : ''
                }`}
                onClick={() => onSelect && onSelect(trade.id)}
              >
                <td className="px-4 py-3 text-gray-700 whitespace-nowrap">
                  {formatDateTime(trade.entry_time)}
                </td>
                <td className="px-4 py-3 font-medium text-gray-800 whitespace-nowrap">
                  {trade.instrument?.symbol || '—'}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  {isLong ? (
                    <span className="direction-long text-sm font-bold">▲ Long</span>
                  ) : (
                    <span className="direction-short text-sm font-bold">▼ Short</span>
                  )}
                </td>
                <td className="px-4 py-3 text-gray-700 whitespace-nowrap">
                  {trade.volume ?? '—'}
                </td>
                <td className="px-4 py-3 text-gray-700 whitespace-nowrap">
                  {trade.entry_price != null ? `$${Number(trade.entry_price).toFixed(2)}` : '—'}
                </td>
                <td className="px-4 py-3 text-gray-700 whitespace-nowrap">
                  {trade.exit_price != null ? `$${Number(trade.exit_price).toFixed(2)}` : '—'}
                </td>
                <td className={`px-4 py-3 whitespace-nowrap font-semibold ${
                  pnlNum > 0 ? 'pnl-positive' : pnlNum < 0 ? 'pnl-negative' : 'text-gray-500'
                }`}>
                  {pnlNum != null ? `$${pnlNum.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
                </td>
                <td className="px-4 py-3 text-gray-500 text-xs whitespace-nowrap">
                  {formatDuration(trade.entry_time, trade.exit_time)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap">
                  {trade.strategy_tag ? (
                    <span className="inline-block bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-full">
                      {trade.strategy_tag}
                    </span>
                  ) : (
                    <span className="text-gray-300">—</span>
                  )}
                </td>
                <td className="px-4 py-3 text-right whitespace-nowrap">
                  <div className="inline-flex items-center gap-1">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        if (onDelete) onDelete(trade.id);
                      }}
                      className="p-1.5 text-gray-400 hover:text-negative hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete trade"
                    >
                      <Trash2 size={15} />
                    </button>
                    <ChevronRight size={15} className="text-gray-300" />
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
