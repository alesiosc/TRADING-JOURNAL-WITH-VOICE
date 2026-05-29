import { useState, useRef } from 'react';
import {
  Upload, FileText, CheckCircle, AlertCircle, Loader2,
  Download, Table, ArrowRight, X, ArrowLeft
} from 'lucide-react';
import { uploadCsv } from '../api/client';

const SAMPLE_CSV = `instrument,direction,volume,entry_price,exit_price,entry_time,exit_time,commission,strategy_tag,notes
EURUSD,long,10000,1.0850,1.0920,2024-01-15T08:30:00,2024-01-15T14:00:00,3.50,breakout,Good momentum trade
AAPL,short,500,195.50,188.20,2024-01-16T10:00:00,2024-01-16T15:30:00,1.00,scalp,Fast move on earnings
BTCUSD,long,0.5,43000,45600,2024-01-17T09:00:00,2024-01-17T16:00:00,0,swing,Held through dip`;

const KNOWN_FIELDS = [
  { key: 'instrument', label: 'Instrument', required: true, aliases: ['symbol', 'ticker', 'pair', 'asset', 'market'] },
  { key: 'direction', label: 'Direction', required: true, aliases: ['side', 'type', 'action', 'order type', 'buy/sell'] },
  { key: 'volume', label: 'Volume', required: true, aliases: ['size', 'qty', 'quantity', 'shares', 'contracts', 'lots', 'amount'] },
  { key: 'entry_price', label: 'Entry Price', required: true, aliases: ['entry', 'open price', 'open', 'price', 'fill price'] },
  { key: 'exit_price', label: 'Exit Price', required: false, aliases: ['exit', 'close price', 'close'] },
  { key: 'entry_time', label: 'Entry Date/Time', required: false, aliases: ['entry date', 'open time', 'entry datetime', 'open date', 'date', 'time', 'timestamp'] },
  { key: 'exit_time', label: 'Exit Date/Time', required: false, aliases: ['exit date', 'close time', 'exit datetime', 'close date'] },
  { key: 'commission', label: 'Commission', required: false, aliases: ['fee', 'fees', 'cost', 'costs'] },
  { key: 'strategy_tag', label: 'Strategy Tag', required: false, aliases: ['strategy', 'tag', 'setup', 'pattern'] },
  { key: 'notes', label: 'Notes', required: false, aliases: ['note', 'comment', 'remarks', 'description', 'journal'] },
  { key: 'broker', label: 'Broker', required: false, aliases: ['platform', 'source'] },
  { key: 'pnl', label: 'P&L', required: false, aliases: ['profit', 'loss', 'result', 'pl', 'realized'] },
];

function autoDetectMapping(csvHeaders) {
  const mapping = {};
  const normalizedHeaders = csvHeaders.map(h => h.trim().toLowerCase());

  for (const field of KNOWN_FIELDS) {
    const exactIdx = normalizedHeaders.indexOf(field.key);
    if (exactIdx !== -1) { mapping[field.key] = csvHeaders[exactIdx]; continue; }

    for (const alias of field.aliases) {
      const idx = normalizedHeaders.indexOf(alias);
      if (idx !== -1) { mapping[field.key] = csvHeaders[idx]; break; }
    }

    // Partial match fallback
    if (!mapping[field.key]) {
      for (let i = 0; i < normalizedHeaders.length; i++) {
        const h = normalizedHeaders[i];
        if (h.includes(field.key) || field.aliases.some(a => h.includes(a))) {
          mapping[field.key] = csvHeaders[i];
          break;
        }
      }
    }
  }
  return mapping;
}

function parseCSV(text) {
  const lines = text.split('\n').filter(l => l.trim());
  if (lines.length < 2) return { headers: [], rows: [], errors: ['Not enough rows'] };

  const headers = lines[0].split(',').map(h => h.trim());
  const errors = [];
  const rows = [];

  for (let i = 1; i < lines.length; i++) {
    const values = lines[i].split(',').map(v => v.trim());
    if (values.length !== headers.length) {
      errors.push(`Row ${i + 1}: column count mismatch (expected ${headers.length}, got ${values.length})`);
      continue;
    }
    const row = {};
    headers.forEach((h, idx) => { row[h] = values[idx]; });
    rows.push(row);
  }

  return { headers, rows, errors, totalRows: rows.length + errors.length };
}

const STEPS = [
  { num: 1, label: 'Upload' },
  { num: 2, label: 'Map' },
  { num: 3, label: 'Preview' },
  { num: 4, label: 'Import' },
];

export default function ImportCsv() {
  const [step, setStep] = useState(1);
  const [csvText, setCsvText] = useState('');
  const [parsed, setParsed] = useState(null);
  const [mapping, setMapping] = useState({});
  const [preview, setPreview] = useState(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleFile = (file) => {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target.result;
      setCsvText(text);
      const result = parseCSV(text);
      setParsed(result);
      if (result.headers.length > 0) {
        setMapping(autoDetectMapping(result.headers));
        setStep(2);
      }
    };
    reader.readAsText(file);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleDragOver = (e) => { e.preventDefault(); setDragOver(true); };
  const handleDragLeave = () => setDragOver(false);

  const handlePreview = async () => {
    const blob = new Blob([csvText], { type: 'text/csv' });
    const file = new File([blob], 'import.csv', { type: 'text/csv' });
    const res = await uploadCsv(file, true);
    if (res.error) {
      setImportResult({ success: false, message: res.error });
      return;
    }
    setPreview(res.data);
    setStep(3);
  };

  const handleImport = async () => {
    setImporting(true);
    setImportResult(null);
    const blob = new Blob([csvText], { type: 'text/csv' });
    const file = new File([blob], 'import.csv', { type: 'text/csv' });
    const res = await uploadCsv(file, false);
    if (res.error) {
      setImportResult({ success: false, message: res.error });
    } else {
      setImportResult({ success: true, data: res.data });
    }
    setImporting(false);
    setStep(4);
  };

  const reset = () => {
    setStep(1);
    setCsvText('');
    setParsed(null);
    setMapping({});
    setPreview(null);
    setImportResult(null);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-[#111827]">CSV Import</h1>
        <p className="text-sm text-[#6B7280] mt-0.5">Import trades from any broker CSV export</p>
      </div>

      {/* Steps indicator */}
      <div className="flex items-center gap-2">
        {STEPS.map((s, i) => (
          <div key={s.num} className="flex items-center gap-2">
            <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
              step === s.num ? 'bg-[#EFF6FF] text-[#2563EB]' :
              step > s.num ? 'bg-[#ECFDF5] text-[#059669]' : 'bg-[#F3F4F6] text-[#9CA3AF]'
            }`}>
              {step > s.num ? <CheckCircle size={12} /> : <span>{s.num}</span>}
              {s.label}
            </div>
            {i < STEPS.length - 1 && <ArrowRight size={14} className="text-[#D1D5DB]" />}
          </div>
        ))}
      </div>

      {/* Step 1: Upload */}
      {step === 1 && (
        <div
          className={`ghost-card text-center py-12 cursor-pointer transition-colors ${
            dragOver ? 'border-[#3B82F6] bg-[#EFF6FF]' : ''
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => handleFile(e.target.files[0])}
          />
          <Upload size={36} className="mx-auto mb-3 text-[#D1D5DB]" />
          <h3 className="text-base font-semibold text-[#6B7280] mb-1">Upload your CSV</h3>
          <p className="text-sm text-[#9CA3AF] mb-4">Drop a file or click to browse</p>
          <button className="btn-ghost-primary" onClick={(e) => { e.stopPropagation(); fileInputRef.current?.click(); }}>
            <Upload size={14} /> Select CSV File
          </button>
        </div>
      )}

      {/* Step 2: Column Mapping */}
      {step === 2 && parsed && (
        <div className="ghost-card">
          <div className="ghost-card-header">
            <h3 className="ghost-card-title"><Table size={16} className="text-[#3B82F6]" /> Map Columns</h3>
            <span className="pill-gray">{parsed.headers.length} columns detected</span>
          </div>

          <div className="space-y-2 mb-5">
            {KNOWN_FIELDS.map((field) => (
              <div key={field.key} className="flex items-center gap-3 text-sm">
                <span className="w-32 text-[#4B5563] font-medium shrink-0">
                  {field.label}
                  {field.required && <span className="text-[#DC2626] ml-0.5">*</span>}
                </span>
                <select
                  value={mapping[field.key] || ''}
                  onChange={(e) => setMapping((m) => ({ ...m, [field.key]: e.target.value }))}
                  className="ghost-select flex-1"
                >
                  <option value="">— Skip —</option>
                  {parsed.headers.map((h) => (
                    <option key={h} value={h}>{h}</option>
                  ))}
                </select>
              </div>
            ))}
          </div>

          <div className="flex justify-between">
            <button onClick={() => setStep(1)} className="btn-ghost-secondary"><ArrowLeft size={14} /> Back</button>
            <button onClick={handlePreview} className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-[#3B82F6] hover:bg-blue-600 rounded-lg transition-colors">
              Preview &amp; Validate <ArrowRight size={14} />
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Preview */}
      {step === 3 && preview && (
        <div className="ghost-card">
          <div className="ghost-card-header">
            <h3 className="ghost-card-title"><FileText size={16} className="text-[#3B82F6]" /> Preview</h3>
            <div className="flex items-center gap-2">
              <span className="pill-green">{preview.success_count ?? 0} valid</span>
              {(preview.error_count ?? 0) > 0 && <span className="pill-red">{preview.error_count} errors</span>}
              <span className="pill-gray">{preview.total_rows ?? 0} rows</span>
            </div>
          </div>

          {/* Sample rows */}
          {preview.rows && preview.rows.length > 0 && (
            <div className="overflow-x-auto mb-4 border border-[#E5E7EB] rounded-xl">
              <table className="ghost-table text-xs">
                <thead>
                  <tr>
                    {Object.keys(preview.rows[0]).map((k) => (
                      <th key={k}>{k}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {preview.rows.slice(0, 5).map((row, i) => (
                    <tr key={i}>
                      {Object.values(row).map((v, j) => (
                        <td key={j} className="max-w-[120px] truncate">{String(v ?? '')}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {preview.errors && preview.errors.length > 0 && (
            <div className="bg-[#FEF2F2] border border-[#FECACA] rounded-xl p-3 mb-4">
              <p className="text-xs font-medium text-[#DC2626] mb-1">Errors:</p>
              {preview.errors.map((err, i) => (
                <p key={i} className="text-xs text-[#DC2626] flex items-start gap-1.5">
                  <AlertCircle size={12} className="shrink-0 mt-0.5" /> {err}
                </p>
              ))}
            </div>
          )}

          <div className="flex justify-between">
            <button onClick={() => setStep(2)} className="btn-ghost-secondary"><ArrowLeft size={14} /> Back to Mapping</button>
            <button
              onClick={handleImport}
              disabled={importing || (preview.error_count > 0)}
              className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-[#3B82F6] hover:bg-blue-600 disabled:bg-blue-300 rounded-lg transition-colors"
            >
              {importing ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
              Import {preview.success_count ?? 0} Trades
            </button>
          </div>
        </div>
      )}

      {/* Step 4: Result */}
      {step === 4 && (
        <div className="ghost-card text-center py-10">
          {importResult?.success ? (
            <>
              <CheckCircle size={40} className="mx-auto mb-3 text-[#059669]" />
              <h3 className="text-base font-semibold text-[#111827] mb-1">Import Complete</h3>
              <p className="text-sm text-[#6B7280] mb-4">
                {importResult.data?.success_count ?? 0} trades imported successfully.
                {importResult.data?.error_count > 0 && ` ${importResult.data.error_count} errors.`}
              </p>
            </>
          ) : (
            <>
              <AlertCircle size={40} className="mx-auto mb-3 text-[#DC2626]" />
              <h3 className="text-base font-semibold text-[#111827] mb-1">Import Failed</h3>
              <p className="text-sm text-[#6B7280] mb-4">{importResult?.message || 'Unknown error'}</p>
            </>
          )}
          <button onClick={reset} className="btn-ghost-primary">
            <Upload size={14} /> Import Another File
          </button>
        </div>
      )}

      {/* Sample CSV download */}
      {step === 1 && (
        <div className="ghost-card">
          <div className="ghost-card-header">
            <h3 className="ghost-card-title"><Download size={16} className="text-[#3B82F6]" /> Sample CSV Format</h3>
          </div>
          <pre className="text-xs text-[#4B5563] bg-[#F9FAFB] border border-[#E5E7EB] rounded-xl p-3 overflow-x-auto whitespace-pre">{SAMPLE_CSV}</pre>
          <button
            onClick={() => {
              const blob = new Blob([SAMPLE_CSV], { type: 'text/csv' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = 'trading-journal-sample.csv';
              a.click();
              URL.revokeObjectURL(url);
            }}
            className="btn-ghost-secondary mt-3"
          >
            <Download size={14} /> Download sample
          </button>
        </div>
      )}
    </div>
  );
}
