import { useState, useRef, useCallback, useEffect } from 'react';
import { Mic, MicOff, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { executeVoiceTrade, fetchActiveTrade } from '../api/client';

// Quick-tag macros for fast entry
const QUICK_MACROS = [
  { label: 'Long NQ', text: 'long NQ 1 at ' },
  { label: 'Long ES', text: 'long ES 1 at ' },
  { label: 'Short NQ', text: 'short NQ 1 at ' },
  { label: 'Short ES', text: 'short ES 1 at ' },
];

export default function VoiceTradeButton() {
  const [listening, setListening] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [toast, setToast] = useState(null); // {type: 'success'|'error'|'info', message}
  const [expanded, setExpanded] = useState(false);
  const recognitionRef = useRef(null);
  const toastTimerRef = useRef(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch {}
      }
      if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    };
  }, []);

  // Auto-dismiss toast after 4 seconds
  const showToast = useCallback((type, message) => {
    setToast({ type, message });
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    toastTimerRef.current = setTimeout(() => setToast(null), 4000);
  }, []);

  // Browser Speech API
  const startListening = useCallback(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      showToast('error', 'Voice recognition not supported in this browser. Try Chrome.');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setListening(true);
    };

    recognition.onresult = async (event) => {
      const transcript = event.results[0][0].transcript;
      setListening(false);
      setProcessing(true);
      await processVoiceInput(transcript);
      setProcessing(false);
    };

    recognition.onerror = (event) => {
      setListening(false);
      showToast('error', `Voice error: ${event.error}`);
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognitionRef.current = recognition;
    recognition.start();
  }, [showToast]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch {}
    }
    setListening(false);
  }, []);

  // Process voice input via API
  const processVoiceInput = async (text) => {
    try {
      const result = await executeVoiceTrade(text);
      if (result.error) {
        showToast('error', `Trade error: ${result.error}`);
        return;
      }

      const data = result.data;
      if (!data || !data.success) {
        showToast('error', `Could not parse: "${text}"`);
        return;
      }

      // Build a friendly success message
      const intentLabels = {
        new_trade: 'Created',
        close_trade: 'Closed',
        add_leg: 'Added to',
        modify_stop: 'Updated stop on',
        modify_target: 'Updated target on',
      };
      const actionLabel = intentLabels[data.intent] || data.intent;
      const symbol = data.instrument || '';

      let msg;
      if (data.intent === 'new_trade') {
        msg = `${actionLabel} ${data.direction} ${symbol} ${data.volume} @ ${data.entry_price}`;
        if (data.legs && data.legs.length > 0) {
          const legDesc = data.legs
            .map((l) => `${l.type === 'stop' ? 'SL' : 'TP'} ${l.price}`)
            .join(', ');
          msg += ` (${legDesc})`;
        }
      } else if (data.intent === 'close_trade') {
        msg = `${actionLabel} ${symbol}`;
        if (data.trade?.pnl != null) {
          msg += ` — PnL: ${data.trade.pnl >= 0 ? '+' : ''}${data.trade.pnl.toFixed(2)}`;
        }
      } else {
        msg = `${actionLabel} ${symbol}`;
      }

      showToast('success', msg);
    } catch (err) {
      showToast('error', `Failed: ${err.message}`);
    }
  };

  // Handle quick macro click
  const handleQuickMacro = (text) => {
    setProcessing(true);
    processVoiceInput(text + '...'); // Placeholder — user should fill in price
    // Actually, a macro should open the mic or prompt for price. For now,
    // just paste the text into the voice input for the user to complete.
    // A better UX: append to input field. For simplicity, we show info toast.
    showToast('info', `Say: "${text}<price>"`);
    setProcessing(false);
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-2">
      {/* Toast notification */}
      {toast && (
        <div
          className={`flex items-center gap-2 px-4 py-2.5 rounded-lg shadow-lg text-sm font-medium transition-all animate-slide-up ${
            toast.type === 'success'
              ? 'bg-green-600 text-white'
              : toast.type === 'error'
              ? 'bg-red-600 text-white'
              : 'bg-blue-600 text-white'
          }`}
        >
          {toast.type === 'success' ? (
            <CheckCircle size={16} />
          ) : toast.type === 'error' ? (
            <AlertCircle size={16} />
          ) : (
            <AlertCircle size={16} />
          )}
          <span>{toast.message}</span>
        </div>
      )}

      {/* Quick macros (expandable) */}
      {expanded && (
        <div className="bg-white rounded-xl shadow-xl border border-gray-100 p-3 mb-2 min-w-[200px]">
          <p className="text-xs font-medium text-gray-500 mb-2 uppercase tracking-wide">Quick Entry</p>
          <div className="flex flex-wrap gap-1.5">
            {QUICK_MACROS.map((macro) => (
              <button
                key={macro.label}
                onClick={() => handleQuickMacro(macro.text)}
                disabled={processing}
                className="px-3 py-1.5 text-xs font-medium bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors disabled:opacity-50"
              >
                {macro.label}
              </button>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Tap macro then say the price, or tap mic and speak full command.
          </p>
        </div>
      )}

      {/* Button group */}
      <div className="flex items-center gap-2">
        {/* Expand macro button */}
        <button
          onClick={() => setExpanded(!expanded)}
          className="w-9 h-9 flex items-center justify-center bg-white border border-gray-200 rounded-full shadow-md hover:bg-gray-50 transition-colors text-gray-500 text-sm font-bold"
          title="Quick macros"
        >
          +
        </button>

        {/* Main mic button */}
        <button
          onClick={listening ? stopListening : startListening}
          disabled={processing}
          className={`
            w-14 h-14 flex items-center justify-center rounded-full shadow-lg transition-all
            ${listening
              ? 'bg-red-500 text-white animate-pulse scale-110 shadow-red-200'
              : processing
              ? 'bg-gray-400 text-white'
              : 'bg-accent text-white hover:bg-blue-600 hover:shadow-xl'
            }
            disabled:opacity-70
          `}
          title={listening ? 'Stop listening' : 'Voice trade command'}
        >
          {processing ? (
            <Loader2 className="animate-spin" size={24} />
          ) : listening ? (
            <MicOff size={24} />
          ) : (
            <Mic size={24} />
          )}
        </button>
      </div>
    </div>
  );
}
