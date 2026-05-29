import { useState, useEffect, useCallback } from 'react';
import { X, Loader2, TrendingUp, TrendingDown } from 'lucide-react';
import { findInstrumentBySymbol, createInstrument } from '../api/client';

const QUICK_INSTRUMENTS = ['ES', 'NQ', 'CL', 'GC', 'EURUSD', 'AAPL', 'MSFT', 'SPY', 'QQQ'];

export default function TradeFormModal({ isOpen, onClose, onSave, trade }) {
  const isEditing = Boolean(trade);

  const [form, setForm] = useState({
    instrument: '',
    direction: 'long',
    volume: '',
    entry_price: '',
    exit_price: '',
    entry_time: '',
    exit_time: '',
    commission: '0',
    strategy_tag: '',
    notes: '',
  });
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [instrumentResolving, setInstrumentResolving] = useState(false);

  useEffect(() => {
    if (isOpen) {
      if (trade) {
        setForm({
          instrument: trade.instrument?.symbol || trade.symbol || '',
          direction: trade.direction || 'long',
          volume: String(trade.volume ?? trade.quantity ?? ''),
          entry_price: String(trade.entry_price ?? ''),
          exit_price: trade.exit_price != null ? String(trade.exit_price) : '',
          entry_time: trade.entry_time ? new Date(trade.entry_time).toISOString().slice(0, 16) : '',
          exit_time: trade.exit_time ? new Date(trade.exit_time).toISOString().slice(0, 16) : '',
          commission: String(trade.commission ?? '0'),
          strategy_tag: trade.strategy_tag || trade.setup_type || '',
          notes: trade.notes || '',
        });
      } else {
        // Default: long, current time
        setForm({
          instrument: '',
          direction: 'long',
          volume: '',
          entry_price: '',
          exit_price: '',
          entry_time: new Date().toISOString().slice(0, 16),
          exit_time: '',
          commission: '0',
          strategy_tag: '',
          notes: '',
        });
      }
      setErrors({});
    }
  }, [isOpen, trade]);

  // ── Keyboard Hotkeys: Ctrl+L = long, Ctrl+S = short ──
  const handleKeyDown = useCallback((e) => {
    if (!isOpen) return;
    if ((e.ctrlKey || e.metaKey) && e.key === 'l') {
      e.preventDefault();
      setForm((f) => ({ ...f, direction: 'long' }));
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      setForm((f) => ({ ...f, direction: 'short' }));
    }
  }, [isOpen]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const update = (field, value) => {
    setForm((f) => ({ ...f, [field]: value }));
    if (errors[field]) setErrors((e) => ({ ...e, [field]: null }));
  };

  const resolveInstrument = async () => {
    const sym = form.instrument.trim().toUpperCase();
    if (!sym) return;
    setInstrumentResolving(true);
    try {
      const res = await findInstrumentBySymbol(sym);
      if (res.error || !res.data) {
        // Auto-create
        const createRes = await createInstrument({ symbol: sym, asset_class: 'futures' });
        if (createRes.error) throw new Error(createRes.error);
      }
    } catch (err) {
      // Non-fatal — will be created on save if needed
    } finally {
      setInstrumentResolving(false);
    }
  };

  const validate = () => {
    const errs = {};
    if (!form.instrument.trim()) errs.instrument = 'Required';
    if (!form.volume || Number(form.volume) <= 0) errs.volume = 'Must be > 0';
    if (!form.entry_price || Number(form.entry_price) <= 0) errs.entry_price = 'Required';
    if (form.exit_price && Number(form.exit_price) <= 0) errs.exit_price = 'Must be > 0';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;
    setSaving(true);
    try {
      await resolveInstrument();
      const payload = {
        instrument_id: 0,
        symbol: form.instrument.trim().toUpperCase(),
        direction: form.direction,
        volume: Number(form.volume),
        quantity: Number(form.volume),
        entry_price: Number(form.entry_price),
        entry_time: form.entry_time ? new Date(form.entry_time).toISOString() : new Date().toISOString(),
        commission: Number(form.commission || 0),
        status: form.exit_price ? 'closed' : 'open',
        strategy_tag: form.strategy_tag.trim() || null,
        setup_type: form.strategy_tag.trim() || null,
        notes: form.notes.trim() || null,
      };
      if (form.exit_price) {
        payload.exit_price = Number(form.exit_price);
        if (form.exit_time) payload.exit_time = new Date(form.exit_time).toISOString();
      }
      await onSave(payload);
      onClose();
    } catch (err) {
      setErrors({ submit: err.message });
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  const direction = form.direction;

  return (
    <div className="fixed inset-0 z-50 modal-overlay flex items-center justify-center p-4" onClick={onClose}>
      <div className="modal-content bg-white rounded-2xl border border-[#E9EDF2] w-full max-w-lg max-h-[90vh] overflow-y-auto" style={{ boxShadow: '0 25px 60px 0 rgba(15, 23, 42, 0.12), 0 0 0 1px rgba(0, 0, 0, 0.03)' }} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4.5 border-b border-[#E9EDF2]">
          <div>
            <h2 className="text-base font-semibold text-[#0F172A]">{isEditing ? 'Edit Trade' : 'New Trade'}</h2>
            <p className="text-xs text-[#64748B] mt-0.5">Ctrl+L = Long · Ctrl+S = Short</p>
          </div>
          <button onClick={onClose} className="p-1.5 text-[#94A3B8] hover:text-[#475569] rounded-lg hover:bg-[#F1F5F9] transition-colors">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4.5">
          {/* Direction toggle */}
          <div>
            <label className="block text-xs font-medium text-[#6B7280] mb-1.5">Direction</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => update('direction', 'long')}
                className={`flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                  direction === 'long'
                    ? 'bg-[#ECFDF5] border-[#A7F3D0] text-[#059669]'
                    : 'bg-white border-[#E5E7EB] text-[#6B7280] hover:bg-[#F9FAFB]'
                }`}
              >
                <TrendingUp size={16} />
                Long
              </button>
              <button
                type="button"
                onClick={() => update('direction', 'short')}
                className={`flex-1 flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                  direction === 'short'
                    ? 'bg-[#FEF2F2] border-[#FECACA] text-[#DC2626]'
                    : 'bg-white border-[#E5E7EB] text-[#6B7280] hover:bg-[#F9FAFB]'
                }`}
              >
                <TrendingDown size={16} />
                Short
              </button>
            </div>
          </div>

          {/* Instrument */}
          <div>
            <label className="block text-xs font-medium text-[#6B7280] mb-1">Instrument <span className="text-[#DC2626]">*</span></label>
            <div className="relative">
              <input
                type="text"
                value={form.instrument}
                onChange={(e) => update('instrument', e.target.value.toUpperCase())}
                placeholder="e.g. ES, NQ, CL"
                className={`ghost-input font-medium ${errors.instrument ? 'border-[#DC2626] ring-1 ring-[#FECACA]' : ''}`}
                list="instr-datalist"
              />
              <datalist id="instr-datalist">
                {QUICK_INSTRUMENTS.map((s) => <option key={s} value={s} />)}
              </datalist>
              {instrumentResolving && <Loader2 size={14} className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-[#9CA3AF]" />}
            </div>
            {errors.instrument && <p className="text-xs text-[#DC2626] mt-1">{errors.instrument}</p>}
          </div>

          {/* Volume + Prices */}
          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Volume <span className="text-[#DC2626]">*</span></label>
              <input type="number" step="any" value={form.volume} onChange={(e) => update('volume', e.target.value)} placeholder="1" className={`ghost-input ${errors.volume ? 'border-[#DC2626] ring-1 ring-[#FECACA]' : ''}`} />
              {errors.volume && <p className="text-xs text-[#DC2626] mt-1">{errors.volume}</p>}
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Entry <span className="text-[#DC2626]">*</span></label>
              <input type="number" step="any" value={form.entry_price} onChange={(e) => update('entry_price', e.target.value)} placeholder="5245.50" className={`ghost-input ${errors.entry_price ? 'border-[#DC2626] ring-1 ring-[#FECACA]' : ''}`} />
              {errors.entry_price && <p className="text-xs text-[#DC2626] mt-1">{errors.entry_price}</p>}
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Exit</label>
              <input type="number" step="any" value={form.exit_price} onChange={(e) => update('exit_price', e.target.value)} placeholder="5278.25" className={`ghost-input ${errors.exit_price ? 'border-[#DC2626] ring-1 ring-[#FECACA]' : ''}`} />
            </div>
          </div>

          {/* Dates */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Entry Time</label>
              <input type="datetime-local" value={form.entry_time} onChange={(e) => update('entry_time', e.target.value)} className="ghost-input" />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Exit Time</label>
              <input type="datetime-local" value={form.exit_time} onChange={(e) => update('exit_time', e.target.value)} className="ghost-input" />
            </div>
          </div>

          {/* Strategy + Commission */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Strategy / Setup</label>
              <input type="text" value={form.strategy_tag} onChange={(e) => update('strategy_tag', e.target.value)} placeholder="breakout, pullback..." className="ghost-input" />
            </div>
            <div>
              <label className="block text-xs font-medium text-[#6B7280] mb-1">Commission</label>
              <input type="number" step="any" value={form.commission} onChange={(e) => update('commission', e.target.value)} className="ghost-input" />
            </div>
          </div>

          {/* Notes */}
          <div>
            <label className="block text-xs font-medium text-[#6B7280] mb-1">Notes</label>
            <textarea value={form.notes} onChange={(e) => update('notes', e.target.value)} rows={2} placeholder="Trade notes..." className="ghost-input resize-none" />
          </div>

          {errors.submit && (
            <div className="bg-[#FEF2F2] text-[#DC2626] text-sm px-3 py-2 rounded-lg border border-[#FECACA]">{errors.submit}</div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-2 pt-4 border-t border-[#E9EDF2]">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm font-medium text-[#64748B] border border-[#E9EDF2] rounded-xl hover:bg-[#F8FAFC] transition-colors">
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="btn-primary"
            >
              {saving ? <Loader2 size={14} className="animate-spin" /> : null}
              {isEditing ? 'Save Changes' : 'Add Trade'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
