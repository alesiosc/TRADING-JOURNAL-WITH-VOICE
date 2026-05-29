import { useState, useMemo } from 'react';
import { ArrowUpDown, ArrowUp, ArrowDown, Trash2, ChevronRight, TrendingUp, TrendingDown } from 'lucide-react';

export default function TradeTable({ trades, onSelect, onDelete, onClose }) {
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
    if (sortField !== field) return <ArrowUpDown size={12} className="ml-1 text-[#D1D5DB]" />;
    return sortDir === 'asc'
      ? <ArrowUp size={12} className="ml-1 text-[#3B82F6]" />
      : <ArrowDown size={12} className="ml-1 text-[#3B82F6]" />;
  };

  const sorted = useMemo(() => {
    return [...trades].sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];
      if (sortField === 'entry_time' || sortField === 'exit_time') {
        aVal = aVal ? new Date(aVal).getTime() : 0;
        bVal = bVal ? new Date(bVal).getTime() : 0;
      }
      if (sortField === 'pnl') {
        aVal = a.pnl ?? 0;
        bVal = b.pnl ?? 0;
      }
      if (sortField === 'volume') {
        aVal = a.volume ?? 0;
        bVal = b.volume ?? 0;
      }
      if (aVal < bVal) return sortDir === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [trades, sortField, sortDir]);

  const formatDate = (iso) => {
    if (!iso) return '\u2014';
    return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  const getDuration = (entry, exit) => {
    if (!entry || !exit) return '\u2014';
    const ms = new Date(exit) - new Date(entry);
    const m = Math.floor(ms / 60000);
    if (m < 60) return `${m}m`;
    const h = Math.floor(m / 60);
    return `${h}h ${m % 60}m`;
  };

  const PnlTag = ({ pnl }) => {
    if (pnl == null) return <span className="text-[#9CA3AF]">\u2014</span>;
    const isPos = pnl > 0;
    const isNeg = pnl < 0;
    return (
      <span className={`inline-flex items-center gap-1 text-sm font-medium ${isPos ? 'text-[#059669]' : isNeg ? 'text-[#DC2626]' : 'text-[#6B7280]'}`}>
        {isPos ? <TrendingUp size={13} /> : isNeg ? <TrendingDown size={13} /> : null}
        {isPos ? '+' : ''}${Number(pnl).toLocaleString(undefined, { minimumFractionDigits: 0 })}
      </span>
    );
  };

  return (
    <div className="ghost-card !p-0 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="ghost-table">
          <thead>
            <tr>
              <th className="cursor-pointer hover:text-[#111827] transition-colors" onClick={() => handleSort('entry_time')}>
                DATE / TIME <SortIcon field="entry_time" />
              </th>
              <th className="cursor-pointer hover:text-[#111827] transition-colors" onClick={() => handleSort('symbol')}>
                INSTRUMENT <SortIcon field="symbol" />
              </th>
              <th>DIR.</th>
              <th className="cursor-pointer hover:text-[#111827] transition-colors" onClick={() => handleSort('volume')}>
                VOL <SortIcon field="volume" />
              </th>
              <th>ENTRY</th>
              <th>EXIT</th>
              <th className="cursor-pointer hover:text-[#111827] transition-colors" onClick={() => handleSort('pnl')}>
                P&L <SortIcon field="pnl" />
              </th>
              <th>DUR</th>
              <th>TAGS</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((trade) => {
              const isLong = trade.direction === 'long';
              const tags = trade.tags || [];
              return (
                <tr
                  key={trade.id}
                  className="cursor-pointer transition-colors"
                  onClick={() => onSelect?.(trade.id)}
                >
                  <td className="text-[#6B7280] text-xs whitespace-nowrap">{formatDate(trade.entry_time)}</td>
                  <td className="font-medium text-[#111827]">{trade.instrument?.symbol || trade.symbol || `#${trade.id}`}</td>
                  <td>
                    <span className={`inline-flex items-center gap-1 text-xs font-medium ${isLong ? 'text-[#059669]' : 'text-[#DC2626]'}`}>
                      {isLong ? '\u25B2' : '\u25BC'} {isLong ? 'Long' : 'Short'}
                    </span>
                  </td>
                  <td className="text-[#4B5563]">{trade.volume ?? trade.quantity ?? '\u2014'}</td>
                  <td className="font-mono text-xs text-[#4B5563]">${Number(trade.entry_price)?.toFixed(2) ?? '\u2014'}</td>
                  <td className="font-mono text-xs text-[#4B5563]">{trade.exit_price != null ? `$${Number(trade.exit_price).toFixed(2)}` : '\u2014'}</td>
                  <td><PnlTag pnl={trade.pnl} /></td>
                  <td className="text-xs text-[#9CA3AF] whitespace-nowrap">{getDuration(trade.entry_time, trade.exit_time)}</td>
                  <td>
                    <div className="flex flex-wrap gap-1">
                      {(trade.setup_type || trade.strategy_tag) && (
                        <span className="pill-outline">{trade.setup_type || trade.strategy_tag}</span>
                      )}
                      {tags.slice(0, 2).map((t) => (
                        <span key={t.id || t.name} className="pill-blue">{t.name}</span>
                      ))}
                      {tags.length > 2 && (
                        <span className="pill-gray">+{tags.length - 2}</span>
                      )}
                    </div>
                  </td>
                  <td>
                    <div className="flex items-center gap-1">
                      {trade.status === 'open' && (
                        <button
                          onClick={(e) => { e.stopPropagation(); onClose?.(trade); }}
                          className="p-1.5 text-[#94A3B8] hover:text-[#059669] hover:bg-[#ECFDF5] rounded-lg transition-colors"
                          title="Close trade"
                        >
                          <TrendingUp size={14} />
                        </button>
                      )}
                      <button
                        onClick={(e) => { e.stopPropagation(); onDelete?.(trade.id); }}
                        className="p-1.5 text-[#D1D5DB] hover:text-[#DC2626] hover:bg-[#FEF2F2] rounded-lg transition-colors"
                        title="Delete trade"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
