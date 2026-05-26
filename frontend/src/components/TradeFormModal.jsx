import { useState, useEffect } from 'react';
import { X, Loader2 } from 'lucide-react';
import { findInstrumentBySymbol, createInstrument } from '../api/client';

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
          instrument: trade.instrument?.symbol || trade.instrument || '',
          direction: trade.direction || 'long',
          volume: trade.volume != null ? String(trade.volume) : '',
          entry_price: trade.entry_price != null ? String(trade.entry_price) : '',
          exit_price: trade.exit_price != null ? String(trade.exit_price) : '',
          entry_time: trade.entry_time ? toDatetimeLocal(trade.entry_time) : '',
          exit_time: trade.exit_time ? toDatetimeLocal(trade.exit_time) : '',
          commission: trade.commission != null ? String(trade.commission) : '0',
          strategy_tag: trade.strategy_tag || '',
          notes: trade.notes || '',
        });
      } else {
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

  const toDatetimeLocal = (iso) => {
    if (!iso) return '';
    const d = new Date(iso);
    const pad = (n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  };

  const handleChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors((prev) => ({ ...prev, [field]: null }));
    }
  };

  const validate = () => {
    const errs = {};
    if (!form.instrument.trim()) errs.instrument = 'Instrument is required';
    if (!form.volume || Number(form.volume) <= 0) errs.volume = 'Volume must be > 0';
    if (!form.entry_price || Number(form.entry_price) <= 0) errs.entry_price = 'Entry price is required';
    if (form.exit_price && Number(form.exit_price) <= 0) errs.exit_price = 'Exit price must be > 0';
    if (!form.entry_time) errs.entry_time = 'Entry date/time is required';
    if (form.commission && Number(form.commission) < 0) errs.commission = 'Commission cannot be negative';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setSaving(true);
    setInstrumentResolving(true);

    try {
      // Resolve instrument symbol → ID
      const symbol = form.instrument.trim();
      let instrumentId;

      const lookup = await findInstrumentBySymbol(symbol);
      if (lookup.error) {
        // Not found — create it
        const created = await createInstrument({
          symbol,
          asset_class: 'futures',
        });
        if (created.error) {
          throw new Error(`Failed to create instrument: ${created.error}`);
        }
        instrumentId = created.data.id;
      } else {
        instrumentId = lookup.data.id;
      }

      setInstrumentResolving(false);

      // Build payload with correct field names
      const payload = {
        instrument_id: instrumentId,
        direction: form.direction,
        volume: Number(form.volume),
        entry_price: Number(form.entry_price),
        entry_time: form.entry_time,
        commission: form.commission ? Number(form.commission) : 0,
        strategy_tag: form.strategy_tag.trim() || null,
        notes: form.notes.trim() || null,
      };

      // Only set exit fields if provided
      if (form.exit_price) payload.exit_price = Number(form.exit_price);
      if (form.exit_time) payload.exit_time = form.exit_time;

      await onSave(payload);
      onClose();
    } catch (err) {
      setErrors({ form: err.message || 'Failed to save trade' });
      setInstrumentResolving(false);
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 modal-overlay">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 className="text-lg font-semibold text-gray-800">
            {isEditing ? 'Edit Trade' : 'New Trade'}
          </h2>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100"
          >
            <X size={20} />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {errors.form && (
            <div className="bg-red-50 text-red-600 text-sm px-4 py-2 rounded-lg">{errors.form}</div>
          )}

          {/* Instrument */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Instrument *</label>
            <input
              type="text"
              value={form.instrument}
              onChange={(e) => handleChange('instrument', e.target.value)}
              placeholder="e.g. EUR/USD, AAPL, BTC"
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 ${
                errors.instrument ? 'border-negative' : 'border-gray-200'
              }`}
            />
            {errors.instrument && <p className="text-xs text-negative mt-1">{errors.instrument}</p>}
          </div>

          {/* Direction */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Direction *</label>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => handleChange('direction', 'long')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium border transition-colors ${
                  form.direction === 'long'
                    ? 'bg-positive/10 border-positive text-positive'
                    : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
              >
                ▲ Long
              </button>
              <button
                type="button"
                onClick={() => handleChange('direction', 'short')}
                className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium border transition-colors ${
                  form.direction === 'short'
                    ? 'bg-negative/10 border-negative text-negative'
                    : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300'
                }`}
              >
                ▼ Short
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Volume */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Volume *</label>
              <input
                type="number"
                step="any"
                value={form.volume}
                onChange={(e) => handleChange('volume', e.target.value)}
                placeholder="1000"
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 ${
                  errors.volume ? 'border-negative' : 'border-gray-200'
                }`}
              />
              {errors.volume && <p className="text-xs text-negative mt-1">{errors.volume}</p>}
            </div>

            {/* Commission */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Commission</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={form.commission}
                onChange={(e) => handleChange('commission', e.target.value)}
                placeholder="0"
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 ${
                  errors.commission ? 'border-negative' : 'border-gray-200'
                }`}
              />
              {errors.commission && <p className="text-xs text-negative mt-1">{errors.commission}</p>}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Entry Price */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Entry Price *</label>
              <input
                type="number"
                step="any"
                value={form.entry_price}
                onChange={(e) => handleChange('entry_price', e.target.value)}
                placeholder="1.0500"
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 ${
                  errors.entry_price ? 'border-negative' : 'border-gray-200'
                }`}
              />
              {errors.entry_price && <p className="text-xs text-negative mt-1">{errors.entry_price}</p>}
            </div>

            {/* Exit Price */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Exit Price</label>
              <input
                type="number"
                step="any"
                value={form.exit_price}
                onChange={(e) => handleChange('exit_price', e.target.value)}
                placeholder="Optional"
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {/* Entry Date/Time */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Entry Date/Time *</label>
              <input
                type="datetime-local"
                value={form.entry_time}
                onChange={(e) => handleChange('entry_time', e.target.value)}
                className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 ${
                  errors.entry_time ? 'border-negative' : 'border-gray-200'
                }`}
              />
              {errors.entry_time && <p className="text-xs text-negative mt-1">{errors.entry_time}</p>}
            </div>

            {/* Exit Date/Time */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Exit Date/Time</label>
              <input
                type="datetime-local"
                value={form.exit_time}
                onChange={(e) => handleChange('exit_time', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
              />
            </div>
          </div>

          {/* Strategy Tag */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Strategy Tag</label>
            <input
              type="text"
              value={form.strategy_tag}
              onChange={(e) => handleChange('strategy_tag', e.target.value)}
              placeholder="e.g. Breakout, Scalp, Swing"
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
            />
          </div>

          {/* Notes */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea
              value={form.notes}
              onChange={(e) => handleChange('notes', e.target.value)}
              rows={3}
              placeholder="Trade notes, reasoning, etc."
              className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 resize-none"
            />
          </div>

          {/* Buttons */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-5 py-2 text-sm font-medium text-white bg-accent hover:bg-blue-600 disabled:bg-blue-300 rounded-lg transition-colors flex items-center gap-2"
            >
              {(saving || instrumentResolving) ? (
                <>
                  <Loader2 className="animate-spin h-4 w-4" />
                  {instrumentResolving ? 'Resolving instrument...' : 'Saving...'}
                </>
              ) : (
                isEditing ? 'Update Trade' : 'Save Trade'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
