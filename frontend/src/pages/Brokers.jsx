import { useState, useEffect } from 'react';
import {
  fetchBrokers, fetchBrokerStatus, syncBroker, syncAllBrokers,
} from '../api/client';
import { RefreshCw, Server, Wifi, WifiOff, Clock, Activity } from 'lucide-react';

const BROKER_ICONS = {
  alpaca: '🗄️',
  ibkr: '🏦',
  ctrader: '💱',
  schwab: '🏛️',
};

const BROKER_DESCRIPTIONS = {
  alpaca: 'US stocks, crypto, options (free tier)',
  ibkr: 'Global multi-asset (requires TWS/Gateway)',
  ctrader: 'Forex, CFDs (Spotware Open API)',
  schwab: 'US equities, options (former TDA)',
};

function StatusBadge({ connected }) {
  return connected ? (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">
      <Wifi size={12} />
      Connected
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 text-xs font-medium text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
      <WifiOff size={12} />
      Disconnected
    </span>
  );
}

function BrokerCard({ broker, onSync, syncing }) {
  const icon = BROKER_ICONS[broker.name] || '🔌';
  const desc = BROKER_DESCRIPTIONS[broker.name] || 'Broker connector';
  const isConnected = broker.status?.connected === true;
  const tradeCount = broker.trade_count || 0;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <span className="text-3xl">{icon}</span>
          <div>
            <h3 className="text-base font-semibold text-gray-800 capitalize">
              {broker.name}
            </h3>
            <p className="text-xs text-gray-400 mt-0.5">{desc}</p>
          </div>
        </div>
        <StatusBadge connected={isConnected} />
      </div>

      {/* Details */}
      <div className="grid grid-cols-2 gap-3 mt-4 pt-3 border-t border-gray-50">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Activity size={14} className="text-gray-400" />
          <span>{tradeCount} trade{tradeCount !== 1 ? 's' : ''} imported</span>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Clock size={14} className="text-gray-400" />
          <span>{broker.last_sync ? broker.last_sync : 'Never synced'}</span>
        </div>
      </div>

      {/* Error state */}
      {broker.status?.error && (
        <div className="mt-3 text-xs text-red-500 bg-red-50 px-3 py-2 rounded-lg">
          {broker.status.error}
        </div>
      )}

      {/* Action */}
      <button
        onClick={() => onSync(broker.name)}
        disabled={syncing}
        className="mt-4 w-full inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-accent border border-accent/30 rounded-lg hover:bg-accent/5 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        <RefreshCw size={14} className={syncing ? 'animate-spin' : ''} />
        {syncing ? 'Syncing...' : 'Sync Now'}
      </button>
    </div>
  );
}

export default function Brokers() {
  const [brokers, setBrokers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [syncing, setSyncing] = useState({});
  const [syncResult, setSyncResult] = useState(null);
  const [syncAllLoading, setSyncAllLoading] = useState(false);

  const loadBrokers = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchBrokers();
      if (res.error) throw new Error(res.error);
      setBrokers(res.data || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBrokers();
  }, []);

  const handleSync = async (name) => {
    setSyncing((prev) => ({ ...prev, [name]: true }));
    setSyncResult(null);
    try {
      const res = await syncBroker(name);
      if (res.error) throw new Error(res.error);
      setSyncResult({ type: 'success', broker: name, data: res.data });
      // Refresh broker list to get updated trade count
      await loadBrokers();
    } catch (err) {
      setSyncResult({ type: 'error', broker: name, error: err.message });
    } finally {
      setSyncing((prev) => ({ ...prev, [name]: false }));
    }
  };

  const handleSyncAll = async () => {
    setSyncAllLoading(true);
    setSyncResult(null);
    try {
      const res = await syncAllBrokers();
      if (res.error) throw new Error(res.error);
      setSyncResult({ type: 'success', broker: 'all', data: res.data });
      await loadBrokers();
    } catch (err) {
      setSyncResult({ type: 'error', broker: 'all', error: err.message });
    } finally {
      setSyncAllLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="flex flex-col items-center gap-3">
          <svg className="animate-spin h-8 w-8 text-accent" viewBox="0 0 24 24" fill="none">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          <p className="text-gray-500 text-sm">Loading broker connections...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-16">
        <div className="text-4xl mb-4">⚠️</div>
        <h2 className="text-lg font-semibold text-gray-600 mb-2">Failed to load brokers</h2>
        <p className="text-sm text-gray-400 mb-4">{error}</p>
        <button
          onClick={loadBrokers}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-accent border border-accent/30 rounded-lg hover:bg-accent/5 transition-colors"
        >
          <RefreshCw size={16} />
          Retry
        </button>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Broker Connections</h1>
          <p className="text-sm text-gray-400 mt-0.5">
            Sync trades from your connected brokerage accounts
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={loadBrokers}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm text-gray-500 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
          <button
            onClick={handleSyncAll}
            disabled={syncAllLoading || brokers.length === 0}
            className="inline-flex items-center gap-1.5 px-4 py-1.5 text-sm font-medium text-white bg-accent rounded-lg hover:bg-accent/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <RefreshCw size={14} className={syncAllLoading ? 'animate-spin' : ''} />
            {syncAllLoading ? 'Syncing...' : 'Sync All'}
          </button>
        </div>
      </div>

      {/* Sync result notification */}
      {syncResult && (
        <div
          className={`mb-6 px-4 py-3 rounded-lg text-sm ${
            syncResult.type === 'success'
              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
              : 'bg-red-50 text-red-600 border border-red-200'
          }`}
        >
          {syncResult.type === 'success' ? (
            syncResult.broker === 'all' ? (
              <div>
                <strong>Sync complete:</strong>
                <ul className="mt-1 space-y-1">
                  {(syncResult.data?.results || []).map((r, i) => (
                    <li key={i}>
                      <span className="capitalize">{r.broker}</span>: {r.imported} imported, {r.skipped} skipped
                      {r.errors?.length > 0 && ` (${r.errors.length} errors)`}
                      {r.duration_seconds > 0 && ` in ${r.duration_seconds}s`}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <span>
                <strong>{syncResult.broker}</strong>: {syncResult.data?.imported || 0} trades imported,{' '}
                {syncResult.data?.skipped || 0} skipped
                {syncResult.data?.errors?.length > 0 && `, ${syncResult.data.errors.length} errors`}
                {syncResult.data?.duration_seconds > 0 && ` (${syncResult.data.duration_seconds}s)`}
              </span>
            )
          ) : (
            <span><strong>Sync error:</strong> {syncResult.error}</span>
          )}
        </div>
      )}

      {/* Empty state */}
      {brokers.length === 0 && (
        <div className="text-center py-20 bg-white rounded-2xl shadow-sm border border-gray-100">
          <div className="text-6xl mb-4">🔌</div>
          <h2 className="text-xl font-semibold text-gray-600 mb-2">No brokers configured</h2>
          <p className="text-gray-400 max-w-md mx-auto">
            Add your broker API keys to the .env file to connect and sync trades.
            Supported brokers: Alpaca, Interactive Brokers, cTrader, Schwab.
          </p>
        </div>
      )}

      {/* Broker cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {brokers.map((broker) => (
          <BrokerCard
            key={broker.name}
            broker={broker}
            onSync={handleSync}
            syncing={syncing[broker.name]}
          />
        ))}
      </div>

      {/* Legend/setup help */}
      {brokers.length > 0 && (
        <div className="mt-8 p-4 bg-amber-50 border border-amber-200 rounded-xl">
          <h4 className="text-sm font-semibold text-amber-800 mb-2">🔑 Setup Guide</h4>
          <ul className="text-xs text-amber-700 space-y-1">
            <li><strong>Alpaca</strong>: Set <code className="bg-amber-100 px-1 rounded">ALPACA_API_KEY</code> and <code className="bg-amber-100 px-1 rounded">ALPACA_SECRET_KEY</code> in .env</li>
            <li><strong>IBKR</strong>: Run TWS/IB Gateway locally, set <code className="bg-amber-100 px-1 rounded">IBKR_PORT</code> in .env (default 7497)</li>
            <li><strong>cTrader</strong>: Set <code className="bg-amber-100 px-1 rounded">CTRADER_CLIENT_ID</code> and <code className="bg-amber-100 px-1 rounded">CTRADER_CLIENT_SECRET</code> in .env</li>
            <li><strong>Schwab</strong>: Set <code className="bg-amber-100 px-1 rounded">SCHWAB_APP_KEY</code> and <code className="bg-amber-100 px-1 rounded">SCHWAB_APP_SECRET</code> in .env</li>
          </ul>
        </div>
      )}
    </div>
  );
}
