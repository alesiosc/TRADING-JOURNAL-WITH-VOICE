import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Edit, FileText, Image, Plus, X, Mic,
  MicOff, Save, Loader2, Camera, ChevronLeft, ChevronRight,
  Play, Pause, Sparkles, BookOpen, Lightbulb, Activity, Brain, BarChart3,
  Film,
} from 'lucide-react';
import { fetchTrade } from '../api/client';
import {
  fetchJournalEntries,
  createJournalEntry,
  fetchScreenshots,
  createScreenshot,
  fetchAIDebrief,
  createAIDebrief,
} from '../api/client';
import TradeFormModal from '../components/TradeFormModal';

// ---- Helpers ----

const formatDate = (iso) => {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-US', {
    dateStyle: 'medium',
    timeStyle: 'short',
  });
};

const SENTIMENT_COLORS = {
  positive: { bg: 'bg-green-100', text: 'text-green-700', label: 'Positive' },
  negative: { bg: 'bg-red-100', text: 'text-red-700', label: 'Negative' },
  neutral: { bg: 'bg-gray-100', text: 'text-gray-600', label: 'Neutral' },
  anxious: { bg: 'bg-orange-100', text: 'text-orange-700', label: 'Anxious' },
  confident: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Confident' },
};

const SCREENSHOT_TYPE_COLORS = {
  entry: { bg: 'bg-green-100', text: 'text-green-700' },
  mid: { bg: 'bg-blue-100', text: 'text-blue-700' },
  exit: { bg: 'bg-red-100', text: 'text-red-700' },
  manual: { bg: 'bg-gray-100', text: 'text-gray-600' },
};

function getSentimentStyle(sentiment) {
  return SENTIMENT_COLORS[sentiment] || { bg: 'bg-gray-100', text: 'text-gray-600', label: sentiment || 'Unknown' };
}

function getScreenshotTypeStyle(type) {
  return SCREENSHOT_TYPE_COLORS[type] || { bg: 'bg-gray-100', text: 'text-gray-600' };
}

function resolveImageUrl(filePath) {
  if (!filePath) return '';
  if (filePath.startsWith('http://') || filePath.startsWith('https://')) return filePath;
  return `/api${filePath}`;
}

// Helper to sort screenshots for flipbook: entry first, then mid, then exit, then manual
function sortScreenshotsForFlipbook(screenshots) {
  const SORT_PRIORITY = { entry: 1, mid: 2, modification: 3, exit: 4, manual: 5 };
  return [...screenshots].sort((a, b) => {
    const pa = SORT_PRIORITY[a.type] || 99;
    const pb = SORT_PRIORITY[b.type] || 99;
    if (pa !== pb) return pa - pb;
    return new Date(a.captured_at || 0) - new Date(b.captured_at || 0);
  });
}

// Score badge color helper
function getScoreColor(score) {
  if (score == null) return 'bg-gray-100 text-gray-500';
  if (score >= 8) return 'bg-green-100 text-green-700';
  if (score >= 6) return 'bg-blue-100 text-blue-700';
  if (score >= 4) return 'bg-yellow-100 text-yellow-700';
  return 'bg-red-100 text-red-700';
}

function getRatingColor(rating) {
  const colors = {
    Excellent: 'bg-green-100 text-green-700',
    Good: 'bg-blue-100 text-blue-700',
    Average: 'bg-yellow-100 text-yellow-700',
    Poor: 'bg-orange-100 text-orange-700',
    Bad: 'bg-red-100 text-red-700',
  };
  return colors[rating] || 'bg-gray-100 text-gray-600';
}

// ---- Lightbox Component ----

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
    <div
      className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4"
      onClick={onClose}
    >
      <div className="relative max-w-4xl max-h-[90vh] flex flex-col" onClick={(e) => e.stopPropagation()}>
        {/* Toolbar */}
        <div className="flex items-center justify-between mb-2">
          <span className="text-white text-sm">
            {ss.type.charAt(0).toUpperCase() + ss.type.slice(1)} · {formatDate(ss.captured_at)}
          </span>
          <button onClick={onClose} className="text-white/60 hover:text-white p-1">
            <X size={22} />
          </button>
        </div>
        {/* Image */}
        <div className="relative flex items-center">
          {currentIndex > 0 && (
            <button
              onClick={() => onNavigate(currentIndex - 1)}
              className="absolute left-2 z-10 bg-black/40 hover:bg-black/60 text-white p-2 rounded-full"
            >
              <ChevronLeft size={24} />
            </button>
          )}
          <img
            src={resolveImageUrl(ss.file_path)}
            alt={`Screenshot ${currentIndex + 1}`}
            className="max-w-full max-h-[80vh] rounded-lg object-contain"
          />
          {currentIndex < screenshots.length - 1 && (
            <button
              onClick={() => onNavigate(currentIndex + 1)}
              className="absolute right-2 z-10 bg-black/40 hover:bg-black/60 text-white p-2 rounded-full"
            >
              <ChevronRight size={24} />
            </button>
          )}
        </div>
        <p className="text-center text-white/60 text-xs mt-2">
          {currentIndex + 1} / {screenshots.length}
        </p>
      </div>
    </div>
  );
}

// ---- Flipbook Overlay Component ----

function FlipbookOverlay({ screenshots, onClose }) {
  const sorted = useMemo(() => sortScreenshotsForFlipbook(screenshots), [screenshots]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1); // 0.5, 1, 2, 3
  const timerRef = useRef(null);
  const filmstripRef = useRef(null);

  const SPEED_OPTIONS = [
    { label: '0.5×', value: 0.5 },
    { label: '1×', value: 1 },
    { label: '2×', value: 2 },
    { label: '3×', value: 3 },
  ];

  // Interval in ms = 2000 / speed  (at 1× = 2s per slide)
  const getInterval = useCallback(() => 2000 / speed, [speed]);

  const goNext = useCallback(() => {
    setCurrentIndex((prev) => (prev < sorted.length - 1 ? prev + 1 : 0));
  }, [sorted.length]);

  const goPrev = useCallback(() => {
    setCurrentIndex((prev) => (prev > 0 ? prev - 1 : sorted.length - 1));
  }, [sorted.length]);

  const togglePlay = useCallback(() => {
    setIsPlaying((p) => !p);
  }, []);

  // Auto-play timer
  useEffect(() => {
    if (isPlaying && sorted.length > 1) {
      timerRef.current = setInterval(goNext, getInterval());
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    };
  }, [isPlaying, goNext, getInterval, sorted.length]);

  // Keyboard controls
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

  // Scroll filmstrip thumb into view when index changes
  useEffect(() => {
    if (filmstripRef.current) {
      const thumbs = filmstripRef.current.children;
      if (thumbs[currentIndex]) {
        thumbs[currentIndex].scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      }
    }
  }, [currentIndex]);

  if (!sorted.length) return null;

  const ss = sorted[currentIndex];

  return (
    <div
      className="fixed inset-0 z-50 bg-black/90 flex flex-col items-center justify-center p-4"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-5xl max-h-screen flex flex-col items-center"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <div className="flex items-center justify-between w-full mb-3">
          <span className="text-white/70 text-sm flex items-center gap-2">
            <Film size={16} />
            Flipbook · {sorted.length} screenshots
          </span>
          <button onClick={onClose} className="text-white/60 hover:text-white p-1">
            <X size={22} />
          </button>
        </div>

        {/* Main image area */}
        <div className="relative w-full flex items-center justify-center mb-3">
          {/* Prev button (large, on image) */}
          {sorted.length > 1 && (
            <button
              onClick={goPrev}
              className="absolute left-2 z-10 bg-black/40 hover:bg-black/60 text-white p-2.5 rounded-full transition-colors"
              title="Previous (←)"
            >
              <ChevronLeft size={28} />
            </button>
          )}

          <div className="flex items-center justify-center bg-black/40 rounded-lg max-h-[65vh] overflow-hidden">
            <img
              src={resolveImageUrl(ss.file_path)}
              alt={`Screenshot ${currentIndex + 1}`}
              className="max-w-full max-h-[65vh] object-contain rounded-lg"
              onError={(e) => {
                e.target.onerror = null;
                e.target.style.display = 'none';
                e.target.parentElement.innerHTML = '<div class="text-gray-500 text-sm p-8">Image not available</div>';
              }}
            />
          </div>

          {/* Next button (large, on image) */}
          {sorted.length > 1 && (
            <button
              onClick={goNext}
              className="absolute right-2 z-10 bg-black/40 hover:bg-black/60 text-white p-2.5 rounded-full transition-colors"
              title="Next (→)"
            >
              <ChevronRight size={28} />
            </button>
          )}
        </div>

        {/* Image info */}
        <p className="text-white/60 text-xs mb-3">
          {currentIndex + 1} / {sorted.length} ·{' '}
          <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-medium ${getScreenshotTypeStyle(ss.type).bg} ${getScreenshotTypeStyle(ss.type).text}`}>
            {ss.type}
          </span>
          {' · '}{formatDate(ss.captured_at)}
        </p>

        {/* Controls bar */}
        <div className="flex items-center gap-3 mb-4">
          {/* Play / Pause */}
          {sorted.length > 1 && (
            <button
              onClick={togglePlay}
              className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                isPlaying
                  ? 'bg-accent text-white hover:bg-blue-600'
                  : 'bg-white/10 text-white hover:bg-white/20'
              }`}
              title={isPlaying ? 'Pause (Space)' : 'Play (Space)'}
            >
              {isPlaying ? <Pause size={16} /> : <Play size={16} />}
              {isPlaying ? 'Pause' : 'Play'}
            </button>
          )}

          {/* Speed selector */}
          {sorted.length > 1 && (
            <div className="flex items-center gap-1 bg-white/10 rounded-lg p-1">
              {SPEED_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => setSpeed(opt.value)}
                  className={`px-2.5 py-1.5 rounded text-xs font-medium transition-colors ${
                    speed === opt.value
                      ? 'bg-accent text-white'
                      : 'text-white/60 hover:text-white hover:bg-white/10'
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Filmstrip thumbnails */}
        {sorted.length > 1 && (
          <div
            ref={filmstripRef}
            className="flex gap-2 overflow-x-auto pb-2 w-full max-w-4xl scrollbar-thin scrollbar-thumb-gray-600 scrollbar-track-transparent"
            style={{ scrollbarWidth: 'thin' }}
          >
            {sorted.map((s, idx) => (
              <button
                key={s.id}
                onClick={() => setCurrentIndex(idx)}
                className={`shrink-0 w-20 h-14 rounded-md overflow-hidden border-2 transition-all ${
                  idx === currentIndex
                    ? 'border-accent ring-2 ring-accent/40 opacity-100'
                    : 'border-transparent opacity-50 hover:opacity-80'
                }`}
              >
                <img
                  src={resolveImageUrl(s.file_path)}
                  alt={`Thumb ${idx + 1}`}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.style.display = 'none';
                    e.target.parentElement.innerHTML = '<div class="text-gray-600 text-[8px] p-1">N/A</div>';
                  }}
                />
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
  const textareaRef = useRef(null);

  // Voice recognition setup
  const startListening = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError('Voice input is not supported in this browser.');
      return;
    }
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      setContent((prev) => prev + transcript);
    };

    recognition.onerror = (event) => {
      setListening(false);
      if (event.error === 'not-allowed') {
        setError('Microphone access denied. Please allow microphone permissions.');
      }
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
    setError(null);
  }, []);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setListening(false);
  }, []);

  const handleSave = async () => {
    if (!content.trim()) {
      setError('Content is required.');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const res = await createJournalEntry({
        trade_id: tradeId,
        content: content.trim(),
        sentiment: sentiment || null,
        mood_before: moodBefore.trim() || null,
        mood_after: moodAfter.trim() || null,
      });
      if (res.error) throw new Error(res.error);
      onSaved(res.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  // Cleanup recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }
    };
  }, []);

  return (
    <div className="border border-gray-200 rounded-lg p-4 bg-gray-50 space-y-3">
      {error && (
        <div className="bg-red-50 text-red-600 text-sm px-3 py-2 rounded-lg">{error}</div>
      )}

      {/* Content area with voice button */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Journal Entry *</label>
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            rows={3}
            placeholder="What happened in this trade? How did you feel?"
            className="w-full px-3 py-2 pr-10 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30 resize-none"
          />
          <button
            type="button"
            onClick={listening ? stopListening : startListening}
            className={`absolute right-2 bottom-2 p-1.5 rounded-full transition-colors ${
              listening
                ? 'bg-red-100 text-red-600 animate-pulse'
                : 'bg-gray-100 text-gray-400 hover:text-accent hover:bg-accent/10'
            }`}
            title={listening ? 'Stop recording' : 'Voice input (Web Speech API)'}
          >
            {listening ? <MicOff size={16} /> : <Mic size={16} />}
          </button>
        </div>
        {listening && (
          <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
            <span className="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse" />
            Listening... Speak your journal entry
          </p>
        )}
      </div>

      {/* Sentiment */}
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Sentiment</label>
        <select
          value={sentiment}
          onChange={(e) => setSentiment(e.target.value)}
          className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
        >
          {Object.entries(SENTIMENT_COLORS).map(([key, val]) => (
            <option key={key} value={key}>{val.label}</option>
          ))}
        </select>
      </div>

      {/* Mood before/after */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Mood Before</label>
          <input
            type="text"
            value={moodBefore}
            onChange={(e) => setMoodBefore(e.target.value)}
            placeholder="e.g. Focused, Nervous"
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Mood After</label>
          <input
            type="text"
            value={moodAfter}
            onChange={(e) => setMoodAfter(e.target.value)}
            placeholder="e.g. Relieved, Regretful"
            className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent/30"
          />
        </div>
      </div>

      {/* Buttons */}
      <div className="flex justify-end gap-2 pt-1">
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-1.5 text-sm font-medium text-gray-600 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={handleSave}
          disabled={saving || !content.trim()}
          className="inline-flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium text-white bg-accent hover:bg-blue-600 disabled:bg-blue-300 rounded-lg transition-colors"
        >
          {saving ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <Save size={14} />
          )}
          Save Entry
        </button>
      </div>
    </div>
  );
}

// ---- AI Debrief Card Component ----

function AiDebriefCard({ tradeId }) {
  const [debrief, setDebrief] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasFetched, setHasFetched] = useState(false);

  const triggerAnalysis = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await createAIDebrief(tradeId);
      if (res.error) throw new Error(res.error);
      setDebrief(res.data?.data || res.data);
      setHasFetched(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // On mount, try to fetch cached debrief silently
  useEffect(() => {
    (async () => {
      const res = await fetchAIDebrief(tradeId);
      if (res.data?.data) {
        setDebrief(res.data.data);
        setHasFetched(true);
      }
    })();
  }, [tradeId]);

  // If no cached debrief and not loading, show the trigger button
  if (!hasFetched && !loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles size={18} className="text-purple-500" />
            <h3 className="text-sm font-semibold text-gray-700">AI Trade Debrief</h3>
          </div>
          <button
            onClick={triggerAnalysis}
            disabled={loading}
            className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-white bg-gradient-to-r from-purple-500 to-blue-500 hover:from-purple-600 hover:to-blue-600 rounded-lg transition-all shadow-sm hover:shadow-md disabled:opacity-60 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <Loader2 size={14} className="animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles size={14} />
                Analyze with AI
              </>
            )}
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          Get AI-powered analysis of your trade including entry/exit quality, risk management, emotional state, and lessons learned. Powered by local Ollama.
        </p>
      </div>
    );
  }

  // Loading state
  if (loading && !debrief) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <div className="flex items-center justify-center gap-2 py-4">
          <Loader2 size={18} className="animate-spin text-purple-500" />
          <span className="text-sm text-gray-500">Analyzing trade with AI...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error && !debrief) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-red-200 p-6 mb-6">
        <div className="flex items-start gap-3">
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-red-700 flex items-center gap-2">
              <Sparkles size={16} />
              AI Debrief Error
            </h3>
            <p className="text-sm text-red-600 mt-1">{error}</p>
            <p className="text-xs text-red-400 mt-1">
              Make sure Ollama is running locally (ollama run qwen3.5:9b) and try again.
            </p>
          </div>
          <button
            onClick={triggerAnalysis}
            className="shrink-0 px-3 py-1.5 text-xs font-medium text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Results display
  if (!debrief) return null;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Sparkles size={18} className="text-purple-500" />
          <h3 className="text-sm font-semibold text-gray-700">AI Trade Debrief</h3>
        </div>
        <div className="flex items-center gap-3">
          {/* Overall Score Badge */}
          <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-bold ${getScoreColor(debrief.overall_score)}`}>
            <BarChart3 size={14} />
            Score: {debrief.overall_score}/10
          </span>
          <button
            onClick={triggerAnalysis}
            disabled={loading}
            className="inline-flex items-center gap-1 px-2.5 py-1 text-xs font-medium text-purple-600 border border-purple-200 rounded-lg hover:bg-purple-50 transition-colors disabled:opacity-50"
            title="Regenerate analysis"
          >
            {loading ? (
              <Loader2 size={12} className="animate-spin" />
            ) : (
              <Sparkles size={12} />
            )}
            Refresh
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {/* Analysis paragraph */}
        {debrief.analysis && (
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <BookOpen size={13} />
              Analysis
            </h4>
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{debrief.analysis}</p>
          </div>
        )}

        {/* Entry & Exit ratings */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="border border-gray-100 rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1">
                <Activity size={12} />
                Entry
              </h4>
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium ${getRatingColor(debrief.entry_rating)}`}>
                {debrief.entry_rating}
              </span>
            </div>
          </div>
          <div className="border border-gray-100 rounded-lg p-3">
            <div className="flex items-center justify-between mb-1">
              <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider flex items-center gap-1">
                <Activity size={12} />
                Exit
              </h4>
              <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-[11px] font-medium ${getRatingColor(debrief.exit_rating)}`}>
                {debrief.exit_rating}
              </span>
            </div>
          </div>
        </div>

        {/* Risk Management */}
        {debrief.risk_management && (
          <div className="border border-gray-100 rounded-lg p-3">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Brain size={13} />
              Risk Management
            </h4>
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{debrief.risk_management}</p>
          </div>
        )}

        {/* Emotional State */}
        {debrief.emotional_state && (
          <div className="border border-gray-100 rounded-lg p-3">
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Activity size={13} />
              Emotional State
            </h4>
            <p className="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{debrief.emotional_state}</p>
          </div>
        )}

        {/* Lessons Learned */}
        {debrief.lessons_learned && debrief.lessons_learned.length > 0 && (
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5 flex items-center gap-1.5">
              <Lightbulb size={13} />
              Lessons Learned
            </h4>
            <ul className="space-y-1.5">
              {debrief.lessons_learned.map((lesson, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="shrink-0 w-5 h-5 flex items-center justify-center rounded-full bg-purple-100 text-purple-700 text-[10px] font-bold mt-0.5">
                    {i + 1}
                  </span>
                  {lesson}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

// ---- Main TradeDetail Page ----

export default function TradeDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [trade, setTrade] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);

  // Journal entries state
  const [journalEntries, setJournalEntries] = useState([]);
  const [journalLoading, setJournalLoading] = useState(true);
  const [showJournalForm, setShowJournalForm] = useState(false);

  // Screenshots state
  const [screenshots, setScreenshots] = useState([]);
  const [screenshotsLoading, setScreenshotsLoading] = useState(true);
  const [lightboxIndex, setLightboxIndex] = useState(null);
  const [flipbookOpen, setFlipbookOpen] = useState(false);
  const [uploadingScreenshot, setUploadingScreenshot] = useState(false);
  const fileInputRef = useRef(null);

  const loadTrade = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchTrade(id);
      if (res.error) throw new Error(res.error);
      setTrade(res.data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadJournalEntries = async () => {
    setJournalLoading(true);
    try {
      const res = await fetchJournalEntries({ trade_id: id });
      if (!res.error) {
        setJournalEntries(res.data);
      }
    } finally {
      setJournalLoading(false);
    }
  };

  const loadScreenshots = async () => {
    setScreenshotsLoading(true);
    try {
      const res = await fetchScreenshots({ trade_id: id });
      if (!res.error) {
        setScreenshots(res.data);
      }
    } finally {
      setScreenshotsLoading(false);
    }
  };

  useEffect(() => {
    if (id) {
      loadTrade();
      loadJournalEntries();
      loadScreenshots();
    }
  }, [id]);

  const handleSaveTrade = async () => {
    await loadTrade();
  };

  const handleJournalEntrySaved = (entry) => {
    setJournalEntries((prev) => [entry, ...prev]);
    setShowJournalForm(false);
  };

  const handleScreenshotUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadingScreenshot(true);
    try {
      const formData = new FormData();
      formData.append('trade_id', String(id));
      formData.append('type', 'manual');
      formData.append('file', file);
      const res = await createScreenshot(formData);
      if (res.error) throw new Error(res.error);
      setScreenshots((prev) => [res.data, ...prev]);
    } catch (err) {
      console.error('Failed to upload screenshot:', err);
    } finally {
      setUploadingScreenshot(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const pnlNum = trade ? (trade.pnl != null ? Number(trade.pnl) : null) : null;
  const isLong = trade?.direction === 'long';

  // ------- Render loading / error -------

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="flex flex-col items-center gap-3">
          <Loader2 className="animate-spin h-7 w-7 text-accent" />
          <p className="text-gray-400 text-sm">Loading trade...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <div className="text-4xl mb-4">⚠️</div>
        <h2 className="text-lg font-semibold text-gray-600 mb-2">Trade not found</h2>
        <p className="text-sm text-gray-400 mb-4">{error}</p>
        <button
          onClick={() => navigate('/trades')}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-accent border border-accent/30 rounded-lg hover:bg-accent/5"
        >
          <ArrowLeft size={16} />
          Back to Trades
        </button>
      </div>
    );
  }

  if (!trade) return null;

  // ------- Render main page -------

  return (
    <div>
      {/* Back button */}
      <button
        onClick={() => navigate('/trades')}
        className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 mb-4 transition-colors"
      >
        <ArrowLeft size={16} />
        Back to Trades
      </button>

      {/* Trade header */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold text-gray-800">
                {trade.instrument?.symbol || trade.instrument || `Trade #${trade.id}`}
              </h1>
              <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                isLong ? 'bg-positive/10 text-positive' : 'bg-negative/10 text-negative'
              }`}>
                {isLong ? '▲ Long' : '▼ Short'}
              </span>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                trade.status === 'closed' ? 'bg-gray-100 text-gray-600' : 'bg-yellow-50 text-yellow-700'
              }`}>
                {trade.status === 'closed' ? 'Closed' : 'Open'}
              </span>
            </div>
            {trade.strategy_tag && (
              <span className="inline-block bg-blue-50 text-blue-700 text-xs px-2 py-0.5 rounded-full">
                {trade.strategy_tag}
              </span>
            )}
          </div>
          <button
            onClick={() => setModalOpen(true)}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-sm font-medium text-accent border border-accent/20 rounded-lg hover:bg-accent/5 transition-colors"
          >
            <Edit size={15} />
            Edit
          </button>
        </div>

        {/* Trade details grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-6">
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Volume</p>
            <p className="text-lg font-semibold text-gray-800 mt-1">{trade.volume ?? '—'}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Entry Price</p>
            <p className="text-lg font-semibold text-gray-800 mt-1">
              {trade.entry_price != null ? `$${Number(trade.entry_price).toFixed(2)}` : '—'}
            </p>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Exit Price</p>
            <p className="text-lg font-semibold text-gray-800 mt-1">
              {trade.exit_price != null ? `$${Number(trade.exit_price).toFixed(2)}` : '—'}
            </p>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">P&amp;L</p>
            <p className={`text-lg font-bold mt-1 ${pnlNum > 0 ? 'pnl-positive' : pnlNum < 0 ? 'pnl-negative' : 'text-gray-500'}`}>
              {pnlNum != null ? `$${pnlNum.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : '—'}
            </p>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Entry Date</p>
            <p className="text-sm text-gray-700 mt-1">{formatDate(trade.entry_time)}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Exit Date</p>
            <p className="text-sm text-gray-700 mt-1">{formatDate(trade.exit_time)}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Commission</p>
            <p className="text-sm text-gray-700 mt-1">{trade.commission != null ? `$${Number(trade.commission).toFixed(2)}` : '—'}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">P&amp;L %</p>
            <p className={`text-sm font-semibold mt-1 ${pnlNum > 0 ? 'text-positive' : pnlNum < 0 ? 'text-negative' : 'text-gray-500'}`}>
              {trade.pnl_pct != null ? `${Number(trade.pnl_pct).toFixed(2)}%` : '—'}
            </p>
          </div>
          {trade.notes && (
            <div className="col-span-2 md:col-span-4">
              <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Notes</p>
              <p className="text-sm text-gray-700 mt-1 whitespace-pre-wrap">{trade.notes}</p>
            </div>
          )}
        </div>
      </div>

      {/* ================================================================ */}
      {/* AI Trade Debrief Section (OPTIONAL — user must click button)     */}
      {/* ================================================================ */}
      <AiDebriefCard tradeId={id} />

      {/* ================================================================ */}
      {/* Journal Entries Section                                          */}
      {/* ================================================================ */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <FileText size={16} className="text-accent" />
            Journal Entries
            {journalEntries.length > 0 && (
              <span className="text-xs font-normal text-gray-400">({journalEntries.length})</span>
            )}
          </h3>
          {!showJournalForm && (
            <button
              onClick={() => setShowJournalForm(true)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-accent border border-accent/20 rounded-lg hover:bg-accent/5 transition-colors"
            >
              <Plus size={14} />
              Add Entry
            </button>
          )}
        </div>

        {/* Inline add form */}
        {showJournalForm && (
          <div className="mb-4">
            <JournalEntryForm
              tradeId={id}
              onSaved={handleJournalEntrySaved}
              onCancel={() => setShowJournalForm(false)}
            />
          </div>
        )}

        {/* Journal entries list */}
        {journalLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 size={18} className="animate-spin text-gray-400" />
          </div>
        ) : journalEntries.length === 0 ? (
          <div className="text-center py-8 text-gray-400 text-sm border-2 border-dashed border-gray-100 rounded-lg">
            <FileText size={32} className="mx-auto mb-2 text-gray-300" />
            <p>No journal entries yet.</p>
            <p className="text-xs mt-1">Add your first entry to track your trading psychology.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {journalEntries.map((entry) => {
              const sentStyle = getSentimentStyle(entry.sentiment);
              return (
                <div key={entry.id} className="border border-gray-100 rounded-lg p-4 hover:border-gray-200 transition-colors">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-800 whitespace-pre-wrap">{entry.content}</p>
                      {entry.voice_transcript && (
                        <p className="text-xs text-gray-400 mt-1 italic">
                          🎤 Voice transcript: {entry.voice_transcript}
                        </p>
                      )}
                    </div>
                    <span className={`shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${sentStyle.bg} ${sentStyle.text}`}>
                      {sentStyle.label}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                    <span>{formatDate(entry.created_at)}</span>
                    {entry.mood_before && (
                      <span>Before: <span className="text-gray-500 font-medium">{entry.mood_before}</span></span>
                    )}
                    {entry.mood_after && (
                      <span>After: <span className="text-gray-500 font-medium">{entry.mood_after}</span></span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ================================================================ */}
      {/* Screenshots Section                                              */}
      {/* ================================================================ */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <Image size={16} className="text-accent" />
            Screenshots
            {screenshots.length > 0 && (
              <span className="text-xs font-normal text-gray-400">({screenshots.length})</span>
            )}
          </h3>
          <div className="flex items-center gap-2">
            {/* Flipbook button — only show when there are screenshots */}
            {screenshots.length > 0 && (
              <button
                onClick={() => setFlipbookOpen(true)}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-purple-600 bg-purple-50 border border-purple-200 rounded-lg hover:bg-purple-100 transition-colors"
              >
                <Film size={14} />
                ▶ Replay
              </button>
            )}
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={handleScreenshotUpload}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploadingScreenshot}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-accent border border-accent/20 rounded-lg hover:bg-accent/5 transition-colors disabled:opacity-50"
            >
              {uploadingScreenshot ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <Camera size={14} />
              )}
              Add Screenshot
            </button>
          </div>
        </div>

        {screenshotsLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 size={18} className="animate-spin text-gray-400" />
          </div>
        ) : screenshots.length === 0 ? (
          <div className="text-center py-8 text-gray-400 text-sm border-2 border-dashed border-gray-100 rounded-lg">
            <Image size={32} className="mx-auto mb-2 text-gray-300" />
            <p>No screenshots captured yet.</p>
            <p className="text-xs mt-1">Add screenshots of your charts to review your setups.</p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              {screenshots.map((ss, idx) => {
                const typeStyle = getScreenshotTypeStyle(ss.type);
                return (
                  <div
                    key={ss.id}
                    className="group relative rounded-lg overflow-hidden border border-gray-200 cursor-pointer hover:border-accent/50 transition-colors"
                    onClick={() => setLightboxIndex(idx)}
                  >
                    <div className="aspect-video bg-gray-100 flex items-center justify-center overflow-hidden">
                      <img
                        src={resolveImageUrl(ss.file_path)}
                        alt={`Screenshot ${idx + 1}`}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                        onError={(e) => {
                          e.target.onerror = null;
                          e.target.src = '';
                          e.target.parentElement.innerHTML = '<div class="text-gray-300 text-xs p-4">Image<br/>not found</div>';
                        }}
                      />
                    </div>
                    <div className="absolute top-1.5 left-1.5">
                      <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${typeStyle.bg} ${typeStyle.text}`}>
                        {ss.type}
                      </span>
                    </div>
                    <div className="px-2 py-1.5 bg-white border-t border-gray-100">
                      <p className="text-[10px] text-gray-400 truncate">{formatDate(ss.captured_at)}</p>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Lightbox */}
            <Lightbox
              screenshots={screenshots}
              currentIndex={lightboxIndex}
              onClose={() => setLightboxIndex(null)}
              onNavigate={(idx) => {
                if (idx >= 0 && idx < screenshots.length) {
                  setLightboxIndex(idx);
                }
              }}
            />

            {/* Flipbook */}
            {flipbookOpen && (
              <FlipbookOverlay
                screenshots={screenshots}
                onClose={() => setFlipbookOpen(false)}
              />
            )}
          </>
        )}
      </div>

      {/* Edit modal */}
      <TradeFormModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        onSave={handleSaveTrade}
        trade={trade}
      />
    </div>
  );
}
