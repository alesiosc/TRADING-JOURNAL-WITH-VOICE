import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Edit, FileText, Image, Plus, X, Mic,
  MicOff, Save, Loader2, Camera, ChevronLeft, ChevronRight,
  Play, Pause, Film, TrendingUp, TrendingDown,
} from 'lucide-react';
import { fetchTrade } from '../api/client';
import {
  fetchJournalEntries,
  createJournalEntry,
  fetchScreenshots,
  createScreenshot,
} from '../api/client';
import TradeFormModal from '../components/TradeFormModal';

// ---- Helpers ----

const formatDate = (iso) => {
  if (!iso) return '\u2014';
  return new Date(iso).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' });
};

function resolveImageUrl(filePath) {
  if (!filePath) return '';
  if (filePath.startsWith('http://') || filePath.startsWith('https://')) return filePath;
  return `/api${filePath}`;
}

function sortScreenshotsForFlipbook(screenshots) {
  const SORT_PRIORITY = { entry: 1, mid: 2, modification: 3, exit: 4, manual: 5 };
  return [...screenshots].sort((a, b) => {
    const pa = SORT_PRIORITY[a.type] || 99;
    const pb = SORT_PRIORITY[b.type] || 99;
    if (pa !== pb) return pa - pb;
    return new Date(a.captured_at || 0) - new Date(b.captured_at || 0);
  });
}

const sentimentPill = {
  positive: 'pill-green',
  negative: 'pill-red',
  neutral: 'pill-gray',
  anxious: 'pill-orange',
  confident: 'pill-blue',
};

function sentPill(s) { return sentimentPill[s] || 'pill-gray'; }

const ssTypePill = {
  entry: 'pill-green',
  mid: 'pill-blue',
  exit: 'pill-red',
  manual: 'pill-gray',
};

function ssPill(t) { return ssTypePill[t] || 'pill-gray'; }

// ---- Lightbox ----

function Lightbox({ screenshots, currentIndex, onClose, onNavigate }) {
  if (currentIndex == null || !screenshots.length) return null;
  const ss = screenshots[currentIndex];

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') onClose();
    if (e.key === 'ArrowLeft') onNavigate(currentIndex - 1);
    if (e.key === 'ArrowRight') onNavigate(currentIndex + 1);
  }, [currentIndex, onClose, onNavigate]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4" onClick={onClose}>
      <div className="relative max-w-5xl max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between mb-2">
          <span className="flex items-center gap-2">
            <span className={ssPill(ss.type)}>{ss.type}</span>
            <span className="text-white/60 text-xs">{formatDate(ss.captured_at)}</span>
          </span>
          <button onClick={onClose} className="text-white/50 hover:text-white p-1"><X size={20} /></button>
        </div>
        <div className="relative flex items-center">
          {currentIndex > 0 && (
            <button onClick={() => onNavigate(currentIndex - 1)} className="absolute left-2 z-10 bg-black/40 hover:bg-black/60 text-white p-2 rounded-full">
              <ChevronLeft size={24} />
            </button>
          )}
          <img src={resolveImageUrl(ss.file_path)} alt={`Screenshot ${currentIndex + 1}`} className="max-w-full max-h-[80vh] rounded-lg object-contain" />
          {currentIndex < screenshots.length - 1 && (
            <button onClick={() => onNavigate(currentIndex + 1)} className="absolute right-2 z-10 bg-black/40 hover:bg-black/60 text-white p-2 rounded-full">
              <ChevronRight size={24} />
            </button>
          )}
        </div>
        <p className="text-center text-white/50 text-xs mt-2">{currentIndex + 1} / {screenshots.length}</p>
      </div>
    </div>
  );
}

// ---- Flipbook ----

function FlipbookOverlay({ screenshots, onClose }) {
  const sorted = useMemo(() => sortScreenshotsForFlipbook(screenshots), [screenshots]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const timerRef = useRef(null);
  const filmstripRef = useRef(null);

  const SPEED_OPTIONS = [
    { label: '0.5\u00d7', value: 0.5 },
    { label: '1\u00d7', value: 1 },
    { label: '2\u00d7', value: 2 },
    { label: '3\u00d7', value: 3 },
  ];

  const getInterval = useCallback(() => 2000 / speed, [speed]);
  const goNext = useCallback(() => setCurrentIndex((p) => (p < sorted.length - 1 ? p + 1 : 0)), [sorted.length]);
  const goPrev = useCallback(() => setCurrentIndex((p) => (p > 0 ? p - 1 : sorted.length - 1)), [sorted.length]);
  const togglePlay = useCallback(() => setIsPlaying((p) => !p), []);

  useEffect(() => {
    if (isPlaying && sorted.length > 1) {
      timerRef.current = setInterval(goNext, getInterval());
    }
    return () => { if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; } };
  }, [isPlaying, goNext, getInterval, sorted.length]);

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Escape') onClose();
    if (e.key === 'ArrowLeft') goPrev();
    if (e.key === 'ArrowRight') goNext();
    if (e.key === ' ') { e.preventDefault(); togglePlay(); }
  }, [onClose, goPrev, goNext, togglePlay]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  useEffect(() => {
    if (filmstripRef.current) {
      const thumbs = filmstripRef.current.children;
      if (thumbs[currentIndex]) thumbs[currentIndex].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
    }
  }, [currentIndex]);

  if (!sorted.length) return null;
  const ss = sorted[currentIndex];

  return (
    <div className="fixed inset-0 z-50 bg-black/85 flex flex-col items-center justify-center p-4" onClick={onClose}>
      <div className="relative w-full max-w-5xl max-h-screen flex flex-col items-center" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between w-full mb-3">
          <span className="text-white/60 text-sm flex items-center gap-2"><Film size={16} /> Flipbook \u00b7 {sorted.length} screenshots</span>
          <button onClick={onClose} className="text-white/50 hover:text-white p-1"><X size={22} /></button>
        </div>
        <div className="relative w-full flex items-center justify-center mb-3">
          {sorted.length > 1 && (
            <button onClick={goPrev} className="absolute left-2 z-10 bg-black/40 hover:bg-black/60 text-white p-2.5 rounded-full" title="Previous"><ChevronLeft size={28} /></button>
          )}
          <div className="flex items-center justify-center bg-black/30 rounded-lg max-h-[65vh] overflow-hidden">
            <img src={resolveImageUrl(ss.file_path)} alt={`Screenshot ${currentIndex + 1}`} className="max-w-full max-h-[65vh] object-contain rounded-lg"
              onError={(e) => { e.target.onerror = null; e.target.style.display = 'none'; e.target.parentElement.innerHTML = '<div class="text-gray-500 text-sm p-8">Image not available</div>'; }} />
          </div>
          {sorted.length > 1 && (
            <button onClick={goNext} className="absolute right-2 z-10 bg-black/40 hover:bg-black/60 text-white p-2.5 rounded-full" title="Next"><ChevronRight size={28} /></button>
          )}
        </div>
        <p className="text-white/50 text-xs mb-3">{currentIndex + 1} / {sorted.length} \u00b7 <span className={ssPill(ss.type)}>{ss.type}</span> \u00b7 {formatDate(ss.captured_at)}</p>
        <div className="flex items-center gap-3 mb-4">
          {sorted.length > 1 && (
            <button onClick={togglePlay} className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${isPlaying ? 'bg-[#3B82F6] text-white' : 'bg-white/10 text-white hover:bg-white/20'}`}>
              {isPlaying ? <Pause size={16} /> : <Play size={16} />}
              {isPlaying ? 'Pause' : 'Play'}
            </button>
          )}
          {sorted.length > 1 && (
            <div className="flex items-center gap-1 bg-white/10 rounded-lg p-1">
              {SPEED_OPTIONS.map((opt) => (
                <button key={opt.value} onClick={() => setSpeed(opt.value)} className={`px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${speed === opt.value ? 'bg-[#3B82F6] text-white' : 'text-white/60 hover:text-white hover:bg-white/10'}`}>{opt.label}</button>
              ))}
            </div>
          )}
        </div>
        {sorted.length > 1 && (
          <div ref={filmstripRef} className="flex gap-2 overflow-x-auto pb-2 w-full max-w-4xl scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent" style={{ scrollbarWidth: 'thin' }}>
            {sorted.map((s, idx) => (
              <button key={s.id} onClick={() => setCurrentIndex(idx)} className={`shrink-0 w-20 h-14 rounded-md overflow-hidden border-2 transition-all ${idx === currentIndex ? 'border-[#3B82F6] ring-2 ring-[#3B82F6]/40 opacity-100' : 'border-transparent opacity-50 hover:opacity-80'}`}>
                <img src={resolveImageUrl(s.file_path)} alt={`Thumb ${idx + 1}`} className="w-full h-full object-cover"
                  onError={(e) => { e.target.onerror = null; e.target.style.display = 'none'; e.target.parentElement.innerHTML = '<div class="text-gray-600 text-[8px] p-1">N/A</div>'; }} />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ---- Journal Entry Form ----

function JournalEntryForm({ tradeId, onSaved, onCancel }) {
  const [content, setContent] = useState('');
  const [sentiment, setSentiment] = useState('neutral');
  const [moodBefore, setMoodBefore] = useState('');
  const [moodAfter, setMoodAfter] = useState('');
  const [listening, setListening] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const recognitionRef = useRef(null);

  const startListening = useCallback(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { setError('Voice input not supported.'); return; }
    const recognition = new SR();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.onresult = (e) => { let t = ''; for (let i = e.resultIndex; i < e.results.length; i++) t += e.results[i][0].transcript; setContent((p) => p + t); };
    recognition.onerror = (e) => { setListening(false); if (e.error === 'not-allowed') setError('Microphone access denied.'); };
    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
    setError(null);
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) { recognitionRef.current.stop(); recognitionRef.current = null; }
    setListening(false);
  }, []);

  const handleSave = async () => {
    if (!content.trim()) { setError('Content is required.'); return; }
    setSaving(true); setError(null);
    try {
      const res = await createJournalEntry({ trade_id: tradeId, content: content.trim(), sentiment: sentiment || null, mood_before: moodBefore.trim() || null, mood_after: moodAfter.trim() || null });
      if (res.error) throw new Error(res.error);
      onSaved(res.data);
    } catch (err) { setError(err.message); }
    finally { setSaving(false); }
  };

  useEffect(() => () => { if (recognitionRef.current) recognitionRef.current.abort(); }, []);

  return (
    <div className="border border-[#E5E7EB] rounded-xl p-4 bg-[#F9FAFB] space-y-3">
      {error && <div className="bg-[#FEF2F2] text-[#DC2626] text-sm px-3 py-2 rounded-lg">{error}</div>}
      <div>
        <label className="block text-xs font-medium text-[#6B7280] mb-1">Journal Entry *</label>
        <div className="relative">
          <textarea value={content} onChange={(e) => setContent(e.target.value)} rows={3} placeholder="What happened? How did you feel?" className="ghost-input resize-none pr-10" />
          <button type="button" onClick={listening ? stopListening : startListening} className={`absolute right-2 bottom-2 p-1.5 rounded-full transition-colors ${listening ? 'bg-red-100 text-red-600 animate-pulse' : 'bg-white text-[#9CA3AF] hover:text-[#3B82F6] border border-[#E5E7EB]'}`}>
            {listening ? <MicOff size={16} /> : <Mic size={16} />}
          </button>
        </div>
        {listening && <p className="text-xs text-[#DC2626] mt-1 flex items-center gap-1"><span className="w-1.5 h-1.5 bg-[#DC2626] rounded-full animate-pulse" /> Listening...</p>}
      </div>
      <div>
        <label className="block text-xs font-medium text-[#6B7280] mb-1">Sentiment</label>
        <select value={sentiment} onChange={(e) => setSentiment(e.target.value)} className="ghost-select">
          <option value="neutral">Neutral</option>
          <option value="positive">Positive</option>
          <option value="negative">Negative</option>
          <option value="anxious">Anxious</option>
          <option value="confident">Confident</option>
        </select>
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-[#6B7280] mb-1">Mood Before</label>
          <input type="text" value={moodBefore} onChange={(e) => setMoodBefore(e.target.value)} placeholder="e.g. Focused" className="ghost-input" />
        </div>
        <div>
          <label className="block text-xs font-medium text-[#6B7280] mb-1">Mood After</label>
          <input type="text" value={moodAfter} onChange={(e) => setMoodAfter(e.target.value)} placeholder="e.g. Regretful" className="ghost-input" />
        </div>
      </div>
      <div className="flex justify-end gap-2 pt-1">
        <button onClick={onCancel} className="px-3 py-1.5 text-sm font-medium text-[#6B7280] border border-[#E5E7EB] rounded-lg hover:bg-[#F9FAFB] transition-colors">Cancel</button>
        <button onClick={handleSave} disabled={saving || !content.trim()} className="inline-flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium text-white bg-[#3B82F6] hover:bg-blue-600 disabled:bg-blue-300 rounded-lg transition-colors">
          {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
          Save Entry
        </button>
      </div>
    </div>
  );
}

// ---- Main Page ----

export default function TradeDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [trade, setTrade] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);

  const [journalEntries, setJournalEntries] = useState([]);
  const [journalLoading, setJournalLoading] = useState(true);
  const [showJournalForm, setShowJournalForm] = useState(false);

  const [screenshots, setScreenshots] = useState([]);
  const [screenshotsLoading, setScreenshotsLoading] = useState(true);
  const [lightboxIndex, setLightboxIndex] = useState(null);
  const [flipbookOpen, setFlipbookOpen] = useState(false);
  const [uploadingScreenshot, setUploadingScreenshot] = useState(false);
  const fileInputRef = useRef(null);

  const loadTrade = async () => {
    setLoading(true); setError(null);
    try {
      const res = await fetchTrade(id);
      if (res.error) throw new Error(res.error);
      setTrade(res.data);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  const loadJournalEntries = async () => {
    setJournalLoading(true);
    try {
      const res = await fetchJournalEntries({ trade_id: id });
      if (!res.error) setJournalEntries(res.data);
    } finally { setJournalLoading(false); }
  };

  const loadScreenshots = async () => {
    setScreenshotsLoading(true);
    try {
      const res = await fetchScreenshots({ trade_id: id });
      if (!res.error) setScreenshots(res.data);
    } finally { setScreenshotsLoading(false); }
  };

  useEffect(() => { if (id) { loadTrade(); loadJournalEntries(); loadScreenshots(); } }, [id]);

  const handleSaveTrade = async () => { await loadTrade(); };
  const handleJournalEntrySaved = (entry) => { setJournalEntries((p) => [entry, ...p]); setShowJournalForm(false); };

  const handleScreenshotUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingScreenshot(true);
    try {
      const fd = new FormData();
      fd.append('trade_id', String(id));
      fd.append('type', 'manual');
      fd.append('file', file);
      const res = await createScreenshot(fd);
      if (res.error) throw new Error(res.error);
      setScreenshots((p) => [res.data, ...p]);
    } catch (err) { console.error(err); }
    finally { setUploadingScreenshot(false); if (fileInputRef.current) fileInputRef.current.value = ''; }
  };

  const pnlNum = trade ? (trade.pnl != null ? Number(trade.pnl) : null) : null;
  const isLong = trade?.direction === 'long';

  if (loading) {
    return <div className="flex items-center justify-center py-24"><Loader2 className="animate-spin h-7 w-7 text-[#3B82F6]" /><p className="text-sm text-[#9CA3AF] ml-2">Loading trade...</p></div>;
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <h2 className="text-base font-semibold text-[#6B7280]">Trade not found</h2>
        <p className="text-sm text-[#9CA3AF] mb-4">{error}</p>
        <button onClick={() => navigate('/trades')} className="btn-ghost-primary"><ArrowLeft size={16} /> Back</button>
      </div>
    );
  }

  if (!trade) return null;

  return (
    <div className="space-y-5">
      {/* Back */}
      <button onClick={() => navigate('/trades')} className="inline-flex items-center gap-1.5 text-sm text-[#6B7280] hover:text-[#111827] transition-colors">
        <ArrowLeft size={16} /> Back to Trades
      </button>

      {/* Trade Header Card */}
      <div className="ghost-card">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3 flex-wrap">
            <h1 className="text-xl font-bold text-[#111827]">{trade.instrument?.symbol || trade.instrument || `Trade #${trade.id}`}</h1>
            <span className={`inline-flex items-center gap-1 pill ${isLong ? 'pill-green' : 'pill-red'}`}>
              {isLong ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
              {isLong ? 'Long' : 'Short'}
            </span>
            <span className={`pill ${trade.status === 'closed' ? 'pill-gray' : 'pill-orange'}`}>
              <span className={`status-dot ${trade.status === 'closed' ? 'status-dot-closed' : 'status-dot-open'}`} />
              {trade.status === 'closed' ? 'Closed' : 'Open'}
            </span>
            {trade.setup_type && <span className="pill-outline">{trade.setup_type}</span>}
            {trade.strategy_tag && <span className="pill-blue">{trade.strategy_tag}</span>}
          </div>
          <button onClick={() => setModalOpen(true)} className="btn-ghost-primary"><Edit size={14} /> Edit</button>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-5 mt-6">
          <div><p className="stat-label">Volume</p><p className="text-base font-semibold text-[#111827] mt-0.5">{trade.volume ?? '\u2014'}</p></div>
          <div><p className="stat-label">Entry Price</p><p className="text-base font-semibold text-[#111827] mt-0.5">${Number(trade.entry_price)?.toFixed(2) ?? '\u2014'}</p></div>
          <div><p className="stat-label">Exit Price</p><p className="text-base font-semibold text-[#111827] mt-0.5">{trade.exit_price != null ? `$${Number(trade.exit_price).toFixed(2)}` : '\u2014'}</p></div>
          <div><p className="stat-label">P&amp;L</p><p className={`text-base font-bold mt-0.5 ${pnlNum > 0 ? 'pnl-positive' : pnlNum < 0 ? 'pnl-negative' : 'text-[#6B7280]'}`}>{pnlNum != null ? `$${pnlNum.toLocaleString(undefined, { minimumFractionDigits: 2 })}` : '\u2014'}</p></div>
          <div><p className="stat-label">Entry Date</p><p className="text-sm text-[#4B5563] mt-0.5">{formatDate(trade.entry_time)}</p></div>
          <div><p className="stat-label">Exit Date</p><p className="text-sm text-[#4B5563] mt-0.5">{formatDate(trade.exit_time)}</p></div>
          <div><p className="stat-label">Commission</p><p className="text-sm text-[#4B5563] mt-0.5">{trade.commission != null ? `$${Number(trade.commission).toFixed(2)}` : '\u2014'}</p></div>
          <div><p className="stat-label">P&amp;L %</p><p className={`text-sm font-semibold mt-0.5 ${pnlNum > 0 ? 'text-[#059669]' : pnlNum < 0 ? 'text-[#DC2626]' : 'text-[#6B7280]'}`}>{trade.pnl_pct != null ? `${Number(trade.pnl_pct).toFixed(2)}%` : '\u2014'}</p></div>
          {trade.notes && <div className="col-span-2 md:col-span-4"><p className="stat-label">Notes</p><p className="text-sm text-[#4B5563] mt-0.5 whitespace-pre-wrap">{trade.notes}</p></div>}
        </div>
      </div>

      {/* Journal Entries */}
      <div className="ghost-card">
        <div className="ghost-card-header">
          <h3 className="ghost-card-title"><FileText size={16} className="text-[#3B82F6]" /> Journal Entries {journalEntries.length > 0 && <span className="text-xs font-normal text-[#9CA3AF]">({journalEntries.length})</span>}</h3>
          {!showJournalForm && <button onClick={() => setShowJournalForm(true)} className="btn-ghost-primary"><Plus size={14} /> Add Entry</button>}
        </div>

        {showJournalForm && <div className="mb-4"><JournalEntryForm tradeId={id} onSaved={handleJournalEntrySaved} onCancel={() => setShowJournalForm(false)} /></div>}

        {journalLoading ? (
          <div className="flex justify-center py-8"><Loader2 size={18} className="animate-spin text-[#9CA3AF]" /></div>
        ) : journalEntries.length === 0 ? (
          <div className="text-center py-8 text-[#9CA3AF] text-sm border-2 border-dashed border-[#E5E7EB] rounded-xl">
            <FileText size={28} className="mx-auto mb-2 text-[#D1D5DB]" />
            <p>No entries yet.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {journalEntries.map((entry) => (
              <div key={entry.id} className="border border-[#E5E7EB] rounded-xl p-4 hover:border-[#D1D5DB] transition-colors">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm text-[#4B5563] whitespace-pre-wrap flex-1">{entry.content}</p>
                  <span className={`shrink-0 ${entry.sentiment ? sentPill(entry.sentiment) : 'pill-gray'}`}>{entry.sentiment || 'Unknown'}</span>
                </div>
                {entry.voice_transcript && <p className="text-xs text-[#9CA3AF] mt-1 italic">🎤 {entry.voice_transcript}</p>}
                <div className="flex items-center gap-3 mt-2 text-xs text-[#9CA3AF]">
                  <span>{formatDate(entry.created_at)}</span>
                  {entry.mood_before && <span>Before: <span className="text-[#4B5563] font-medium">{entry.mood_before}</span></span>}
                  {entry.mood_after && <span>After: <span className="text-[#4B5563] font-medium">{entry.mood_after}</span></span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Screenshots */}
      <div className="ghost-card">
        <div className="ghost-card-header">
          <h3 className="ghost-card-title"><Image size={16} className="text-[#3B82F6]" /> Screenshots {screenshots.length > 0 && <span className="text-xs font-normal text-[#9CA3AF]">({screenshots.length})</span>}</h3>
          <div className="flex items-center gap-2">
            {screenshots.length > 0 && (
              <button onClick={() => setFlipbookOpen(true)} className="btn-ghost-secondary"><Film size={14} /> ▶ Replay</button>
            )}
            <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleScreenshotUpload} />
            <button onClick={() => fileInputRef.current?.click()} disabled={uploadingScreenshot} className="btn-ghost-primary">
              {uploadingScreenshot ? <Loader2 size={14} className="animate-spin" /> : <Camera size={14} />}
              Add
            </button>
          </div>
        </div>

        {screenshotsLoading ? (
          <div className="flex justify-center py-8"><Loader2 size={18} className="animate-spin text-[#9CA3AF]" /></div>
        ) : screenshots.length === 0 ? (
          <div className="text-center py-8 text-[#9CA3AF] text-sm border-2 border-dashed border-[#E5E7EB] rounded-xl">
            <Image size={28} className="mx-auto mb-2 text-[#D1D5DB]" />
            <p>No screenshots yet.</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              {screenshots.map((ss, idx) => (
                <div key={ss.id} className="group relative rounded-xl overflow-hidden border border-[#E5E7EB] cursor-pointer hover:border-[#3B82F6]/50 transition-colors" onClick={() => setLightboxIndex(idx)}>
                  <div className="aspect-video bg-[#F9FAFB] flex items-center justify-center overflow-hidden">
                    <img src={resolveImageUrl(ss.file_path)} alt={`Screenshot ${idx + 1}`} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                      onError={(e) => { e.target.onerror = null; e.target.src = ''; e.target.parentElement.innerHTML = '<div class="text-gray-300 text-xs p-4">N/A</div>'; }} />
                  </div>
                  <div className="absolute top-1.5 left-1.5"><span className={ssPill(ss.type)}>{ss.type}</span></div>
                  <div className="px-2 py-1.5 bg-white border-t border-[#E5E7EB]"><p className="text-[10px] text-[#9CA3AF] truncate">{formatDate(ss.captured_at)}</p></div>
                </div>
              ))}
            </div>
            <Lightbox screenshots={screenshots} currentIndex={lightboxIndex} onClose={() => setLightboxIndex(null)} onNavigate={(idx) => { if (idx >= 0 && idx < screenshots.length) setLightboxIndex(idx); }} />
            {flipbookOpen && <FlipbookOverlay screenshots={screenshots} onClose={() => setFlipbookOpen(false)} />}
          </>
        )}
      </div>

      <TradeFormModal isOpen={modalOpen} onClose={() => setModalOpen(false)} onSave={handleSaveTrade} trade={trade} />
    </div>
  );
}
