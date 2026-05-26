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

// Known field names our system understands
const KNOWN_FIELDS = [
  { key: 'instrument', label: 'Instrument', required: true, aliases: ['symbol', 'ticker', 'pair', 'asset', 'market'] },
  { key: 'direction', label: 'Direction', required: true, aliases: ['side', 'type', 'action', 'order type', 'buy/sell'] },
  { key: 'volume', label: 'Volume', required: true, aliases: ['size', 'qty', 'quantity', 'shares', 'contracts', 'lots', 'amount'] },
  { key: 'entry_price', label: 'Entry Price', required: true, aliases: ['entry', 'open price', 'open', 'price', 'fill price'] },
  { key: 'exit_price', label: 'Exit Price', required: false, aliases: ['exit', 'close price', 'close'] },
  { key: 'entry_time', label: 'Entry Date/Time', required: false, aliases: ['entry date', 'open time', 'entry datetime', 'open date', 'date', 'time', 'timestamp'] },
  { key: 'exit_time', label: 'Exit Date/Time', required: false, aliases: ['exit date', 'close time', 'exit datetime', 'close date'] },
  { key: 'commission', label: 'Commission', required: false, aliases: ['fee', 'fees', 'cost', 'costs', 'commission'] },
  { key: 'strategy_tag', label: 'Strategy Tag', required: false, aliases: ['strategy', 'tag', 'setup', 'pattern', 'comment'] },
  { key: 'notes', label: 'Notes', required: false, aliases: ['note', 'comment', 'remarks', 'description', 'journal'] },
  { key: 'broker', label: 'Broker', required: false, aliases: ['platform', 'source'] },
  { key: 'pnl', label: 'P&L', required: false, aliases: ['profit', 'loss', 'result', 'pl', 'realized'] },
];

// Auto-detect best field mapping from CSV headers
function autoDetectMapping(csvHeaders) {
  const mapping = {};
  const normalizedHeaders = csvHeaders.map(h => h.trim().toLowerCase());

  for (const field of KNOWN_FIELDS) {
    // Check exact match first
    const exactIdx = normalizedHeaders.indexOf(field.key);
    if (exactIdx !== -1) {
      mapping[field.key] = csvHeaders[exactIdx];
      continue;
    }
    // Check aliases
    let found = false;
    for (const alias of field.aliases) {
      const aliasIdx = normalizedHeaders.indexOf(alias);
      if (aliasIdx !== -1) {
        mapping[field.key] = csvHeaders[aliasIdx];
        found = true;
        break;
      }
    }
    if (!found) {
      // Try partial match
      for (let i = 0; i < normalizedHeaders.length; i++) {
        const h = normalizedHeaders[i];
        if (h.includes(field.key) || field.key.includes(h) ||
            field.aliases.some(a => h.includes(a) || a.includes(h))) {
          mapping[field.key] = csvHeaders[i];
          found = true;
          break;
        }
      }
    }
    if (!found) {
      mapping[field.key] = ''; // Not mapped
    }
  }
  return mapping;
}

// --- Column Mapper Step ---
function ColumnMapper({ csvHeaders, onConfirm, onBack }) {
  const [mapping, setMapping] = useState(() => autoDetectMapping(csvHeaders));
  const unassignedHeaders = csvHeaders.filter(h =>
    !Object.values(mapping).includes(h)
  );

  const handleSelect = (fieldKey, header) => {
    // If this header was already mapped to another field, remove that assignment
    const updated = { ...mapping };
    for (const [k, v] of Object.entries(updated)) {
      if (v === header) updated[k] = '';
    }
    updated[fieldKey] = header;
    setMapping(updated);
  };

  const allRequiredMapped = KNOWN_FIELDS
    .filter(f => f.required)
    .every(f => mapping[f.key]);

  const getFieldValue = (fieldKey) => mapping[fieldKey] || '';

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center gap-2 mb-4">
        <button onClick={onBack} className="p-1 text-gray-400 hover:text-gray-600">
          <ArrowLeft size={18} />
        </button>
        <div>
          <h3 className="text-sm font-semibold text-gray-700">Map CSV Columns</h3>
          <p className="text-xs text-gray-400 mt-0.5">
            Match your CSV columns to journal fields. Required fields marked with *.
          </p>
        </div>
      </div>

      <div className="space-y-2 max-h-[50vh] overflow-y-auto pr-2">
        {KNOWN_FIELDS.map(field => {
          const assigned = getFieldValue(field.key);
          return (
            <div key={field.key} className="flex items-center gap-3 py-1.5">
              {/* Our field name */}
              <div className="w-36 shrink-0 text-right">
                <span className="text-sm font-medium text-gray-700">
                  {field.label}
                  {field.required && <span className="text-red-400 ml-0.5">*</span>}
                </span>
              </div>

              {/* Arrow */}
              <div className="text-gray-300 shrink-0">
                <ArrowRight size={14} />
              </div>

              {/* Dropdown of CSV headers */}
              <div className="flex-1">
                <select
                  value={assigned}
                  onChange={(e) => handleSelect(field.key, e.target.value)}
                  className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 ${
                    field.required && !assigned
                      ? 'border-orange-300 bg-orange-50'
                      : assigned
                      ? 'border-green-200 bg-green-50/30'
                      : 'border-gray-200'
                  }`}
                >
                  <option value="">— Not mapped —</option>
                  {csvHeaders.map(h => (
                    <option key={h} value={h}>{h}</option>
                  ))}
                </select>
              </div>

              {/* Match indicator */}
              <div className="w-5 shrink-0">
                {assigned ? (
                  field.required
                    ? <CheckCircle size={16} className="text-green-500" />
                    : <CheckCircle size={16} className="text-blue-400" />
                ) : (
                  field.required
                    ? <AlertCircle size={16} className="text-orange-400" />
                    : <span className="text-gray-300 text-xs">opt</span>
                )}
              </div>
            </div>
          );
        })}

        {unassignedHeaders.length > 0 && (
          <div className="mt-4 pt-3 border-t border-gray-100">
            <p className="text-xs text-gray-400 mb-2">
              Unmapped columns ({unassignedHeaders.length}):
            </p>
            <div className="flex flex-wrap gap-1.5">
              {unassignedHeaders.map(h => (
                <span key={h} className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">
                  {h}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
        <button
          onClick={onBack}
          className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
        >
          Back
        </button>
        <button
          onClick={() => onConfirm(mapping)}
          disabled={!allRequiredMapped}
          className="px-5 py-2 text-sm font-medium text-white bg-accent hover:bg-blue-600 disabled:bg-blue-300 rounded-lg transition-colors"
        >
          Confirm & Preview
        </button>
      </div>
    </div>
  );
}

// --- Main ImportCsv Page ---
export default function ImportCsv() {
  const [step, setStep] = useState('upload'); // upload | mapping | preview | done
  const [file, setFile] = useState(null);
  const [rawHeaders, setRawHeaders] = useState([]);
  const [parsedRows, setParsedRows] = useState([]);
  const [errors, setErrors] = useState([]);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState(null);
  const [uploadError, setUploadError] = useState(null);
  const [columnMapping, setColumnMapping] = useState({});
  const fileInputRef = useRef(null);

  const KNOWN_HEADERS = KNOWN_FIELDS.map(f => f.key);

  const parseCSV = (text) => {
    const lines = text.split('\n').filter((l) => l.trim());
    if (lines.length < 2) {
      setUploadError('CSV file appears to be empty or has no data rows.');
      return null;
    }

    const headers = lines[0].split(',').map((h) => h.trim().toLowerCase());
    const rows = [];
    const errs = [];

    for (let i = 1; i < lines.length; i++) {
      const vals = lines[i].split(',').map((v) => v.trim());
      const row = {};
      headers.forEach((h, idx) => {
        row[h] = vals[idx] || '';
      });
      rows.push(row);

      // Basic validation
      if (!row.instrument) errs.push(`Row ${i}: missing instrument`);
      if (!row.direction || !['long', 'short'].includes(row.direction.toLowerCase())) {
        errs.push(`Row ${i}: direction must be 'long' or 'short'`);
      }
      if (!row.volume || isNaN(Number(row.volume))) {
        errs.push(`Row ${i}: invalid volume`);
      }
      if (!row.entry_price || isNaN(Number(row.entry_price))) {
        errs.push(`Row ${i}: invalid entry_price`);
      }
    }

    return { rows, errors: errs };
  };

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files?.[0];
    if (!selectedFile) return;

    if (!selectedFile.name.endsWith('.csv')) {
      setUploadError('Please select a .csv file.');
      return;
    }

    setUploadError(null);
    setFile(selectedFile);

    const reader = new FileReader();
    reader.onload = (evt) => {
      const text = evt.target.result;
      const lines = text.split('\n').filter(l => l.trim());
      if (lines.length < 2) {
        setUploadError('CSV file appears to be empty.');
        return;
      }
      const headers = lines[0].split(',').map(h => h.trim());

      // Check if headers need mapping
      const normalizedHeaders = headers.map(h => h.trim().toLowerCase());
      const allKnown = normalizedHeaders.every(h =>
        KNOWN_HEADERS.includes(h) || h === '' || h === 'notes'
      );

      setRawHeaders(headers);

      if (allKnown) {
        // Headers match directly — skip mapping
        const result = parseCSV(text);
        if (result) {
          setParsedRows(result.rows);
          setErrors(result.errors);
          setStep('preview');
        }
      } else {
        // Need mapping — auto-detect and show mapper
        setStep('mapping');
      }
    };
    reader.onerror = () => {
      setUploadError('Failed to read file.');
    };
    reader.readAsText(selectedFile);
  };

  const handleMappingConfirm = (mapping) => {
    setColumnMapping(mapping);

    // Re-read file with mapping applied
    const reader = new FileReader();
    reader.onload = (evt) => {
      const text = evt.target.result;
      // Remap CSV headers using the mapping
      const lines = text.split('\n').filter(l => l.trim());
      const headers = lines[0].split(',').map(h => h.trim().toLowerCase());

      // Create remapped CSV: use our field names
      const reverseMap = {};
      for (const [ourField, theirHeader] of Object.entries(mapping)) {
        if (theirHeader) {
          const idx = headers.indexOf(theirHeader.toLowerCase());
          if (idx !== -1) {
            reverseMap[ourField] = idx;
          }
        }
      }

      // Build remapped rows
      const remappedLines = [KNOWN_HEADERS.join(',')];
      for (let i = 1; i < lines.length; i++) {
        const vals = lines[i].split(',').map(v => v.trim());
        const remapped = KNOWN_HEADERS.map(field => {
          const idx = reverseMap[field];
          return idx !== undefined ? (vals[idx] || '') : '';
        });
        remappedLines.push(remapped.join(','));
      }

      const result = parseCSV(remappedLines.join('\n'));
      if (result) {
        setParsedRows(result.rows);
        setErrors(result.errors);
        setStep('preview');
      }
    };
    reader.readAsText(file);
  };

  const handleImport = async () => {
    if (!file) return;
    setImporting(true);
    setImportResult(null);

    try {
      // First do dry run
      const dryRes = await uploadCsv(file, true);
      if (dryRes.error) {
        setImportResult({ success: false, message: dryRes.error });
        setImporting(false);
        return;
      }

      // Then actual import
      const res = await uploadCsv(file, false);
      if (res.error) {
        setImportResult({ success: false, message: res.error });
      } else {
        setImportResult({ success: true, data: res.data });
        setStep('done');
      }
    } catch (err) {
      setImportResult({ success: false, message: err.message });
    } finally {
      setImporting(false);
    }
  };

  const handleReset = () => {
    setStep('upload');
    setFile(null);
    setParsedRows([]);
    setErrors([]);
    setImportResult(null);
    setUploadError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // Determine preview columns
  const previewColumns = parsedRows.length > 0
    ? Object.keys(parsedRows[0]).filter((k) =>
        ['instrument', 'direction', 'volume', 'entry_price', 'exit_price', 'entry_time', 'exit_time', 'commission', 'strategy_tag'].includes(k)
      )
    : [];

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <Upload size={24} className="text-accent" />
          CSV Import
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Import your trading history from a CSV file. The file must have headers in the first row.
        </p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-6 text-sm">
        {['upload', 'mapping', 'preview', 'done'].map((s, idx) => (
          <div key={s} className="flex items-center gap-2">
            <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold ${
              step === s
                ? 'bg-accent text-white'
                : ['mapping', 'preview'].includes(step) && s === 'upload'
                ? 'bg-green-100 text-green-600'
                : step === 'done' && s !== 'done'
                ? 'bg-green-100 text-green-600'
                : 'bg-gray-100 text-gray-400'
            }`}>
              {step === 'done' && s !== 'done' ? <CheckCircle size={14} /> : idx + 1}
            </span>
            <span className={`capitalize hidden sm:inline ${
              step === s ? 'text-gray-800 font-medium' : 'text-gray-400'
            }`}>
              {s === 'upload' ? 'Upload' : s === 'mapping' ? 'Map Columns' : s === 'preview' ? 'Preview' : 'Import'}
            </span>
            {idx < 3 && <ArrowRight size={14} className="text-gray-300" />}
          </div>
        ))}
      </div>

      {/* ========== Step 1: Upload ========== */}
      {step === 'upload' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8">
          <div
            className="border-2 border-dashed border-gray-200 rounded-xl p-12 text-center hover:border-accent/40 transition-colors cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload size={48} className="mx-auto mb-4 text-gray-300" />
            <h3 className="text-lg font-semibold text-gray-700 mb-2">
              Upload your trading history CSV
            </h3>
            <p className="text-sm text-gray-400 mb-4">
              Drag and drop or click to select a CSV file
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv"
              className="hidden"
              onChange={handleFileSelect}
            />
            <button
              type="button"
              className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-accent hover:bg-blue-600 rounded-lg transition-colors"
            >
              <Upload size={16} />
              Select CSV File
            </button>
          </div>

          {uploadError && (
            <div className="mt-4 bg-red-50 text-red-600 text-sm px-4 py-3 rounded-lg flex items-start gap-2">
              <AlertCircle size={16} className="shrink-0 mt-0.5" />
              <span>{uploadError}</span>
            </div>
          )}

          {/* Sample format */}
          <div className="mt-8">
            <div className="flex items-center gap-2 mb-3">
              <FileText size={16} className="text-gray-400" />
              <h4 className="text-sm font-medium text-gray-600">Sample CSV Format</h4>
              <button
                onClick={() => {
                  const blob = new Blob([SAMPLE_CSV], { type: 'text/csv' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = 'sample_trades.csv';
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="ml-auto inline-flex items-center gap-1 text-xs text-accent hover:text-blue-600"
              >
                <Download size={12} />
                Download sample
              </button>
            </div>
            <pre className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-xs text-gray-600 overflow-x-auto whitespace-pre">
              {SAMPLE_CSV}
            </pre>
            <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-gray-500">
              <div><strong>Required columns:</strong> instrument, direction, volume, entry_price</div>
              <div><strong>Optional columns:</strong> exit_price, entry_time, exit_time, commission, strategy_tag, notes, broker, status, pnl, pnl_pct, rating</div>
            </div>
          </div>
        </div>
      )}

      {/* ========== Step 1.5: Column Mapping ========== */}
      {step === 'mapping' && rawHeaders.length > 0 && (
        <ColumnMapper
          csvHeaders={rawHeaders}
          onConfirm={handleMappingConfirm}
          onBack={handleReset}
        />
      )}

      {/* ========== Step 2: Preview ========== */}
      {step === 'preview' && (
        <div className="space-y-4">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold text-gray-700">Parsed Data Preview</h3>
                <p className="text-xs text-gray-400 mt-0.5">
                  {parsedRows.length} rows found · {errors.length} validation {errors.length === 1 ? 'issue' : 'issues'}
                </p>
              </div>
              <button
                onClick={handleReset}
                className="text-sm text-gray-400 hover:text-gray-600 flex items-center gap-1"
              >
                <X size={14} />
                Change file
              </button>
            </div>

            <div className="overflow-x-auto border border-gray-200 rounded-lg">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-200">
                    <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">#</th>
                    {previewColumns.map((col) => (
                      <th key={col} className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                        {col === 'entry_price' ? 'Entry' : col === 'exit_price' ? 'Exit' : col === 'entry_time' ? 'Entry Time' : col === 'exit_time' ? 'Exit Time' : col}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {parsedRows.slice(0, 20).map((row, i) => (
                    <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
                      <td className="px-3 py-2 text-xs text-gray-400">{i + 1}</td>
                      {previewColumns.map((col) => (
                        <td key={col} className="px-3 py-2 text-sm text-gray-700">
                          {col === 'direction' ? (
                            <span className={`inline-flex items-center gap-1 text-xs font-medium ${
                              row[col]?.toLowerCase() === 'long' ? 'text-positive' : 'text-negative'
                            }`}>
                              {row[col]?.toLowerCase() === 'long' ? '\u25b2' : '\u25bc'} {row[col]}
                            </span>
                          ) : (
                            row[col] || <span className="text-gray-300">\u2014</span>
                          )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {parsedRows.length > 20 && (
                <div className="px-3 py-2 text-xs text-gray-400 border-t border-gray-200 text-center">
                  Showing first 20 of {parsedRows.length} rows
                </div>
              )}
            </div>

            {errors.length > 0 && (
              <div className="mt-4 bg-orange-50 border border-orange-200 rounded-lg p-3">
                <p className="text-xs font-medium text-orange-700 mb-1 flex items-center gap-1">
                  <AlertCircle size={12} />
                  {errors.length} validation {errors.length === 1 ? 'issue' : 'issues'}
                </p>
                <ul className="text-xs text-orange-600 space-y-0.5">
                  {errors.slice(0, 10).map((err, i) => (
                    <li key={i}>{err}</li>
                  ))}
                  {errors.length > 10 && (
                    <li className="text-orange-400">...and {errors.length - 10} more</li>
                  )}
                </ul>
              </div>
            )}

            <div className="mt-4 flex justify-end gap-3">
              <button
                onClick={handleReset}
                className="px-4 py-2 text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleImport}
                disabled={importing}
                className="inline-flex items-center gap-2 px-5 py-2 text-sm font-medium text-white bg-accent hover:bg-blue-600 disabled:bg-blue-300 rounded-lg transition-colors"
              >
                {importing ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    Importing...
                  </>
                ) : (
                  <>
                    <Upload size={16} />
                    Import {parsedRows.length} {parsedRows.length === 1 ? 'Trade' : 'Trades'}
                  </>
                )}
              </button>
            </div>

            {importResult && !importResult.success && (
              <div className="mt-3 bg-red-50 text-red-600 text-sm px-4 py-3 rounded-lg flex items-start gap-2">
                <AlertCircle size={16} className="shrink-0 mt-0.5" />
                <span>{importResult.message}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========== Step 3: Done ========== */}
      {step === 'done' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={32} className="text-green-600" />
          </div>
          <h2 className="text-xl font-bold text-gray-800 mb-2">Import Complete!</h2>
          <p className="text-sm text-gray-500 mb-6">
            {importResult?.data?.imported || parsedRows.length} trades have been imported successfully.
          </p>
          {importResult?.data && (
            <div className="grid grid-cols-2 gap-4 max-w-xs mx-auto mb-6">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-2xl font-bold text-accent">{importResult.data.imported || 0}</p>
                <p className="text-xs text-gray-500">Imported</p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-2xl font-bold text-gray-600">{importResult.data.skipped || 0}</p>
                <p className="text-xs text-gray-500">Skipped</p>
              </div>
            </div>
          )}
          <div className="flex justify-center gap-3">
            <button
              onClick={handleReset}
              className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-accent border border-accent/20 rounded-lg hover:bg-accent/5 transition-colors"
            >
              <Upload size={16} />
              Import Another File
            </button>
            <a
              href="/trades"
              className="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-medium text-white bg-accent hover:bg-blue-600 rounded-lg transition-colors"
            >
              <Table size={16} />
              View Trades
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
