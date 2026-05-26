import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, RefreshCw, Search } from 'lucide-react';
import TradeTable from '../components/TradeTable';
import TradeFormModal from '../components/TradeFormModal';
import {
  fetchTrades,
  createTrade,
  updateTrade,
  deleteTrade,
} from '../api/client';

export default function Trades() {
  const navigate = useNavigate();
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [instrumentSearch, setInstrumentSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [editingTrade, setEditingTrade] = useState(null);

  const loadTrades = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {};
      if (statusFilter) params.status = statusFilter;
      const res = await fetchTrades(params);
      if (res.error) throw new Error(res.error);
      setTrades(res.data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    loadTrades();
  }, [loadTrades]);

  // Apply client-side filters (instrument search, date range)
  const filteredTrades = trades.filter((t) => {
    if (instrumentSearch) {
      const q = instrumentSearch.toLowerCase();
      if (!t.instrument?.symbol?.toLowerCase().includes(q)) return false;
    }
    if (dateFrom && t.entry_time) {
      if (new Date(t.entry_time) < new Date(dateFrom)) return false;
    }
    if (dateTo && t.entry_time) {
      const end = new Date(dateTo);
      end.setHours(23, 59, 59, 999);
      if (new Date(t.entry_time) > end) return false;
    }
    return true;
  });

  const handleNewTrade = () => {
    setEditingTrade(null);
    setModalOpen(true);
  };

  const handleSaveTrade = async (payload) => {
    if (editingTrade) {
      const res = await updateTrade(editingTrade.id, payload);
      if (res.error) throw new Error(res.error);
    } else {
      const res = await createTrade(payload);
      if (res.error) throw new Error(res.error);
    }
    await loadTrades();
  };

  const handleDeleteTrade = async (id) => {
    if (!window.confirm('Are you sure you want to delete this trade?')) return;
    const res = await deleteTrade(id);
    if (res.error) {
      alert('Failed to delete trade: ' + res.error);
      return;
    }
    await loadTrades();
  };

  const handleSelectTrade = (id) => {
    navigate(`/trades/${id}`);
  };

  return (
    <div>
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Trades</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            {trades.length} trade{trades.length !== 1 ? 's' : ''} logged
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={loadTrades}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm text-gray-500 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw size={15} />
            Refresh
          </button>
          <button
            onClick={handleNewTrade}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-accent hover:bg-blue-600 rounded-lg transition-colors"
          >
            <Plus size={16} />
            New Trade
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-4">
        <div className="flex flex-wrap gap-3 items-end">
          {/* Status */}
          <div className="flex-1 min-w-[140px]">
            <label className="block text-xs font-medium text-gray-500 mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-accent/30"
            >
              <option value="">All</option>
              <option value="open">Open</option>
              <option value="closed">Closed</option>
            </select>
          </div>

          {/* Instrument Search */}
          <div className="flex-1 min-w-[160px]">
            <label className="block text-xs font-medium text-gray-500 mb-1">Instrument</label>
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                value={instrumentSearch}
                onChange={(e) => setInstrumentSearch(e.target.value)}
                placeholder="Search..."
                className="w-full pl-8 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
              />
            </div>
          </div>

          {/* Date From */}
          <div className="flex-1 min-w-[140px]">
            <label className="block text-xs font-medium text-gray-500 mb-1">From</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
            />
          </div>

          {/* Date To */}
          <div className="flex-1 min-w-[140px]">
            <label className="block text-xs font-medium text-gray-500 mb-1">To</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
            />
          </div>

          {/* Clear filters */}
          <button
            onClick={() => {
              setStatusFilter('');
              setInstrumentSearch('');
              setDateFrom('');
              setDateTo('');
            }}
            className="px-3 py-2 text-xs text-gray-500 hover:text-gray-700 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Error state */}
      {error && (
        <div className="bg-red-50 text-red-600 text-sm px-4 py-3 rounded-xl mb-4">
          Failed to load trades: {error}
        </div>
      )}

      {/* Loading state */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="flex flex-col items-center gap-3">
            <svg className="animate-spin h-7 w-7 text-accent" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-gray-400 text-sm">Loading trades...</p>
          </div>
        </div>
      ) : (
        <TradeTable
          trades={filteredTrades}
          onSelect={handleSelectTrade}
          onDelete={handleDeleteTrade}
        />
      )}

      {/* Trade Form Modal */}
      <TradeFormModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSave={handleSaveTrade}
        trade={editingTrade}
      />
    </div>
  );
}
