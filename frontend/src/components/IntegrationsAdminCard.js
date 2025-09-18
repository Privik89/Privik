import React, { useEffect, useState } from 'react';

export default function IntegrationsAdminCard() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [toggles, setToggles] = useState({ gmail: false, microsoft365: false, imap: false });

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/ui/integrations/status');
      if (!res.ok) throw new Error(`Status ${res.status}`);
      const data = await res.json();
      setStatus(data);
    } catch (e) {
      setError(`Failed to fetch status: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const startIntegrations = async () => {
    try {
      setSaving(true);
      setError(null);
      const res = await fetch('/api/ui/integrations/start', { method: 'POST' });
      if (!res.ok) throw new Error(`Start ${res.status}`);
      await fetchStatus();
    } catch (e) {
      setError(`Failed to start integrations: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  const reconnect = async () => {
    try {
      setSaving(true);
      setError(null);
      const res = await fetch('/api/ui/integrations/reconnect', { method: 'POST' });
      if (!res.ok) throw new Error(`Reconnect ${res.status}`);
      await fetchStatus();
    } catch (e) {
      setError(`Failed to reconnect: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  const resetState = async (name) => {
    try {
      setSaving(true);
      setError(null);
      const params = new URLSearchParams();
      if (name) params.append('name', name);
      const res = await fetch(`/api/ui/integrations/reset-state?${params.toString()}`, { method: 'POST' });
      if (!res.ok) throw new Error(`Reset ${res.status}`);
      await fetchStatus();
    } catch (e) {
      setError(`Failed to reset state: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  const saveToggles = async () => {
    try {
      setSaving(true);
      setError(null);
      const params = new URLSearchParams();
      Object.entries(toggles).forEach(([k, v]) => params.append(k, v));
      const res = await fetch(`/api/ui/integrations/toggles?${params.toString()}`, { method: 'POST' });
      if (!res.ok) throw new Error(`Toggles ${res.status}`);
    } catch (e) {
      setError(`Failed to save toggles: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  const onToggle = (key) => (e) => {
    setToggles({ ...toggles, [key]: e.target.checked });
  };

  return (
    <div className="bg-white shadow rounded p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold">Email Integrations</h3>
        <div className="flex gap-2">
          <button onClick={fetchStatus} className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded" disabled={loading}>
            {loading ? 'Refreshing…' : 'Refresh'}
          </button>
          <button onClick={startIntegrations} className="px-3 py-1 text-sm bg-privik-blue-600 text-white rounded" disabled={saving}>
            {saving ? 'Starting…' : 'Start Monitoring'}
          </button>
          <button onClick={reconnect} className="px-3 py-1 text-sm bg-gray-800 text-white rounded" disabled={saving}>
            {saving ? 'Working…' : 'Reconnect'}
          </button>
          <button onClick={() => resetState()} className="px-3 py-1 text-sm bg-red-600 text-white rounded" disabled={saving}>
            {saving ? 'Working…' : 'Reset All'}
          </button>
        </div>
      </div>
      {error && <div className="text-red-600 text-sm mb-2">{error}</div>}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        {['gmail', 'microsoft365', 'imap'].map((name) => (
          <div key={name} className="border rounded p-3">
            <div className="text-sm font-medium mb-1 uppercase">{name}</div>
            <div className="text-xs text-gray-500">Connected: {status?.[name]?.connected ? 'Yes' : 'No'}</div>
            <div className="text-xs text-gray-500">Last Sync: {status?.[name]?.last_sync ? new Date(status[name].last_sync).toLocaleString() : 'n/a'}</div>
            <div className="text-xs text-gray-500 mb-2">Errors: {status?.[name]?.errors || 0} (backoff {status?.[name]?.retry_backoff || 0}s)</div>
            <label className="inline-flex items-center gap-2 text-sm">
              <input type="checkbox" checked={toggles[name]} onChange={onToggle(name)} />
              Enable {name}
            </label>
            <div className="mt-2 flex gap-2">
              <button onClick={() => resetState(name)} className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded">Reset</button>
            </div>
          </div>
        ))}
      </div>
      <div className="flex justify-end">
        <button onClick={saveToggles} className="px-3 py-1 text-sm bg-gray-800 text-white rounded" disabled={saving}>
          {saving ? 'Saving…' : 'Save Toggles'}
        </button>
      </div>
    </div>
  );
}


