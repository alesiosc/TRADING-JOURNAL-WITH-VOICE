import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, RefreshCw, Search, X, DollarSign, Loader2 } from 'lucide-react';
import TradeTable from '../components/TradeTable';
import TradeFormModal from '../components/TradeFormModal';
import {
  fetchTrades,
  createTrade,
  updateTrade,
  deleteTrade,
  closeTrade,
} from '../api/client';

export default function Trades() {
  const navigate = useNavigate();
  const [trades, setTrades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [statusFilter, setStatusFilter] = useState('');
  const [instrumentSearch, setInstrumentSearch] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  const [modalOpen, setModalOpen] = useState(false);
  const [editingTrade, setEditingTrade] = useState(null);
  const [closeModal, setCloseModal] = useState(null); // { id, symbol, entry }
  const [closePrice, setClosePrice] = useState('');
  const [closing, setClosing] = useState(false);

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
    if (!window.confirm('Delete this trade?')) return;
    const res = await deleteTrade(id);
    if (res.error) {
      alert('Failed: ' + res.error);
      return;
    }
    await loadTrades();
  };

  const handleSelectTrade = (id) => {
    navigate(`/trades/${id}`);
  };

  const handleQuickClose = async () => {
    if (!closeModal || !closePrice || !parseFloat(closePrice)) return;
    setClosing(true);
    try {
      const res = await closeTrade(closeModal.id, parseFloat(closePrice));
      if (res.error) throw new Error(res.error);
      await loadTrades();
      setCloseModal(null);
      setClosePrice('');
    } catch (err) {
      alert('Failed to close: ' + err.message);
    } finally {
      setClosing(false);
    }
  };

  const openTradesCount = trades.filter(t => t.status === 'open').length;

  return (
    <div>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-[#0F172A] tracking-tight">Trades</h1>
          <p className="text-sm text-[#64748B] mt-1">
            {trades.length} trade{trades.length !== 1 ? 's' : ''} logged
            {openTradesCount > 0 && (
              <span className="ml-2 inline-flex items-center gap-1.5 text-xs">
                <span className="w-1.5 h-1.5 rounded-full bg-[#F59E0B]" />
                {openTradesCount} open
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={loadTrades} className="btn-ghost-secondary">
            <RefreshCw size={14} />
            Refresh
          </button>
          <button onClick={handleNewTrade} className="btn-primary">
            <Plus size={16} />
            New Trade
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="ghost-card !p-4 mb-4">
        <div className="flex flex-wrap gap-3 items-end">
          <div className="flex-1 min-w-[130px]">
            <label className="block text-xs font-medium text-[#6B7280] mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="ghost-select"
            >
              <option value="">All</option>
              <option value="open">Open</option>
              <option value="closed">Closed</option>
            </select>
          </div>
          <div className="flex-1 min-w-[150px]">
            <label className="block text-xs font-medium text-[#6B7280] mb-1">Instrument</label>
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#9CA3AF]" />
              <input
                type="text"
                value={instrumentSearch}
                onChange={(e) => setInstrumentSearch(e.target.value)}
                placeholder="Search..."
                className="ghost-input pl-8"
              />
            </div>
          </div>
          <div className="flex-1 min-w-[130px]">
            <label className="block text-xs font-medium text-[#6B7280] mb-1">From</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="ghost-input"
            />
          </div>
          <div className="flex-1 min-w-[130px]">
            <label className="block text-xs font-medium text-[#6B7280] mb-1">To</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="ghost-input"
            />
          </div>
          <button
            onClick={() => { setStatusFilter(''); setInstrumentSearch(''); setDateFrom(''); setDateTo(''); }}
            className="px-3 py-2 text-xs text-[#6B7280] hover:text-[#111827] border border-[#E5E7EB] rounded-lg hover:bg-[#F9FAFB] transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-[#FEF2F2] text-[#DC2626] text-sm px-4 py-3 rounded-xl mb-4 border border-[#FECACA]">
          Failed to load trades: {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="flex flex-col items-center gap-3">
            <svg className="animate-spin h-7 w-7 text-[#3B82F6]" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-sm text-[#9CA3AF]">Loading trades...</p>
          </div>
        </div>
      ) : (
        <TradeTable
          trades={filteredTrades}
          onSelect={handleSelectTrade}
          onDelete={handleDeleteTrade}
          onClose={(trade) => setCloseModal({ id: trade.id, symbol: trade.instrument?.symbol || trade.symbol, entry: trade.entry_price, direction: trade.direction, volume: trade.volume || trade.quantity })}
        />
      )}

      <TradeFormModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSave={handleSaveTrade}
        trade={editingTrade}
      />

      {/* Quick Close Modal */}
      {closeModal && (
        <div className="fixed inset-0 z-50 modal-overlay flex items-center justify-center p-4" onClick={() => { setCloseModal(null); setClosePrice(''); }}>
          <div className="modal-content bg-white rounded-2xl border border-[#E9EDF2] w-full max-w-sm" style={{ boxShadow: '0 25px 60px 0 rgba(15,23,42,0.12)' }} onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between px-5 py-4 border-b border-[#E9EDF2]">
              <div>
                <h3 className="text-base font-semibold text-[#0F172A]">Close Trade</h3>
                <p className="text-xs text-[#64748B] mt-0.5">{closeModal.symbol} · #{closeModal.id}</p>
              </div>
              <button onClick={() => { setCloseModal(null); setClosePrice(''); }} className="p-1 text-[#94A3B8] hover:text-[#475569] rounded-lg hover:bg-[#F1F5F9]">
                <X size={18} />
              </button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-xs font-medium text-[#64748B] mb-1.5">Entry Price</label>
                <div className="text-sm font-semibold text-[#0F172A]">${Number(closeModal.entry)?.toFixed(2) || '\u2014'}</div>
              </div>
              <div>
                <label className="block text-xs font-medium text-[#64748B] mb-1.5">Exit Price <span className="text-[#DC2626]">*</span></label>
                <div className="relative">
                  <DollarSign size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#94A3B8]" />
                  <input
                    type="number"
                    step="any"
                    value={closePrice}
                    onChange={(e) => setClosePrice(e.target.value)}
                    placeholder="5278.25"
                    className="ghost-input pl-8 text-base font-semibold"
                    autoFocus
                    onKeyDown={(e) => { if (e.key === 'Enter') handleQuickClose(); if (e.key === 'Escape') { setCloseModal(null); setClosePrice(''); } }}
                  />
                </div>
              </div>
              {closePrice && parseFloat(closePrice) && closeModal.entry && (
                <div className="bg-[#F8FAFC] rounded-xl p-3 border border-[#E9EDF2]">
                  <div className="flex justify-between text-sm">
                    <span className="text-[#64748B]">Direction</span>
                    <span className="font-medium text-[#0F172A]">{closeModal.direction === 'long' ? 'Long \u25B2' : 'Short \u25BC'}</span>
                  </div>
                  <div className="flex justify-between text-sm mt-1.5">
                    <span className="text-[#64748B]">Est. P&amp;L</span>
                    <span className={`font-bold ${closeModal.direction === 'long' ? (parseFloat(closePrice) > closeModal.entry ? 'text-[#059669]' : 'text-[#DC2626]') : (parseFloat(closePrice) < closeModal.entry ? 'text-[#059669]' : 'text-[#DC2626]')}`}>
                      {closeModal.direction === 'long'
                        ? `$${((parseFloat(closePrice) - closeModal.entry) * (closeModal.volume || 1) * 50).toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                        : `$${((closeModal.entry - parseFloat(closePrice)) * (closeModal.volume || 1) * 50).toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
                    </span>
                  </div>
                </div>
              )}
              <div className="flex gap-2 justify-end pt-1">
                <button onClick={() => { setCloseModal(null); setClosePrice(''); }} className="px-4 py-2 text-sm font-medium text-[#64748B] border border-[#E9EDF2] rounded-xl hover:bg-[#F8FAFC] transition-colors">
                  Cancel
                </button>
                <button
                  onClick={handleQuickClose}
                  disabled={closing || !closePrice || !parseFloat(closePrice)}
                  className="inline-flex items-center gap-1.5 px-5 py-2 text-sm font-medium text-white rounded-xl transition-all disabled:opacity-50"
                  style={{ background: closePrice && parseFloat(closePrice) > 0 ? 'linear-gradient(135deg, #059669, #10B981)' : 'linear-gradient(135deg, #DC2626, #EF4444)' }}
                >
                  {closing ? <Loader2 size={14} className="animate-spin" /> : null}
                  {closing ? 'Closing...' : 'Close Trade'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
