const BASE_URL = import.meta.env.VITE_API_URL || '/api';

async function request(url, options = {}) {
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  // Don't set Content-Type for FormData (let browser set it)
  if (options.body instanceof FormData) {
    delete config.headers['Content-Type'];
  }

  try {
    const response = await fetch(`${BASE_URL}${url}`, config);
    if (!response.ok) {
      const errorBody = await response.text();
      let errorMessage;
      try {
        const parsed = JSON.parse(errorBody);
        errorMessage = parsed.detail || parsed.message || errorBody;
      } catch {
        errorMessage = errorBody || `HTTP ${response.status}`;
      }
      return { data: null, error: errorMessage };
    }
    const text = await response.text();
    const data = text ? JSON.parse(text) : null;
    return { data, error: null };
  } catch (err) {
    return { data: null, error: err.message || 'Network error' };
  }
}

// ---- Trades ----

export function fetchTrades(params = {}) {
  const query = new URLSearchParams();
  if (params.status) query.set('status', params.status);
  if (params.skip != null) query.set('skip', String(params.skip));
  if (params.limit != null) query.set('limit', String(params.limit));
  const qs = query.toString();
  return request(`/trades/${qs ? `?${qs}` : ''}`);
}

export function fetchTrade(id) {
  return request(`/trades/${id}/`);
}

export function createTrade(data) {
  return request('/trades/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function updateTrade(id, data) {
  return request(`/trades/${id}/`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export function deleteTrade(id) {
  return request(`/trades/${id}/`, {
    method: 'DELETE',
  });
}

// ---- Stats ----

export function fetchStatsSummary(params = {}) {
  const query = new URLSearchParams();
  if (params.instrument_id) query.set('instrument_id', params.instrument_id);
  if (params.start_date) query.set('start_date', params.start_date);
  if (params.end_date) query.set('end_date', params.end_date);
  const qs = query.toString();
  return request(`/stats/summary${qs ? `?${qs}` : ''}`);
}

export function fetchEquityCurve() {
  return request('/stats/equity-curve');
}

export function fetchByInstrument() {
  return request('/stats/by-instrument');
}

export function fetchByMonth() {
  return request('/stats/by-month');
}

// ---- Journal Entries ----

export function fetchJournalEntries(params = {}) {
  const query = new URLSearchParams();
  if (params.trade_id != null) query.set('trade_id', String(params.trade_id));
  if (params.sentiment) query.set('sentiment', params.sentiment);
  if (params.skip != null) query.set('skip', String(params.skip));
  if (params.limit != null) query.set('limit', String(params.limit));
  const qs = query.toString();
  return request(`/journal/${qs ? `?${qs}` : ''}`);
}

export function createJournalEntry(data) {
  return request('/journal/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ---- Screenshots ----

export function fetchScreenshots(params = {}) {
  const query = new URLSearchParams();
  if (params.trade_id != null) query.set('trade_id', String(params.trade_id));
  if (params.type) query.set('type', params.type);
  if (params.skip != null) query.set('skip', String(params.skip));
  if (params.limit != null) query.set('limit', String(params.limit));
  const qs = query.toString();
  return request(`/screenshots/${qs ? `?${qs}` : ''}`);
}

export function createScreenshot(data) {
  // data should be FormData with file + fields
  return request('/screenshots/', {
    method: 'POST',
    body: data,
  });
}

// ---- Import ----

export function uploadCsv(file, dryRun = true) {
  const formData = new FormData();
  formData.append('file', file);
  const query = dryRun ? '?dry_run=true' : '';
  return request(`/import/csv${query}`, {
    method: 'POST',
    body: formData,
  });
}

// ---- Instruments ----

export function fetchInstruments(search = '') {
  const qs = search ? `?search=${encodeURIComponent(search)}` : '';
  return request(`/instruments/${qs}`);
}

export function createInstrument(data) {
  return request('/instruments/', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export function findInstrumentBySymbol(symbol) {
  return request(`/instruments/by-symbol/${encodeURIComponent(symbol)}`);
}

// ---- AI (Debrief & Daily Summary) ----

export function fetchAIDebrief(tradeId) {
  return request(`/ai/debrief/${tradeId}`);
}

export function createAIDebrief(tradeId) {
  return request(`/ai/debrief/${tradeId}`, {
    method: 'POST',
  });
}

export function createDailySummary(date) {
  const qs = date ? `?date=${encodeURIComponent(date)}` : '';
  return request(`/ai/daily-summary${qs}`, {
    method: 'POST',
  });
}

// ---- Health ----

export function fetchHealth() {
  return request('/health');
}
