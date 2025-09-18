import React, { useEffect, useState } from 'react';

export default function SandboxAdminCard() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [detonateLoading, setDetonateLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      // Use UI proxy that does not require HMAC from browser
      const res = await fetch('/api/ui/sandbox/status');
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
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setDetonateLoading(true);
      setError(null);
      setResult(null);
      const form = new FormData();
      form.append('file', file);
      const res = await fetch('/api/ui/sandbox/detonate-test', {
        method: 'POST',
        body: form,
      });
      if (!res.ok) throw new Error(`Status ${res.status}`);
      const data = await res.json();
      setResult(data);
    } catch (e) {
      setError(`Detonation failed: ${e.message}`);
    } finally {
      setDetonateLoading(false);
    }
  };

  return (
    <div className="bg-white shadow rounded p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold">Sandbox Administration</h3>
        <button
          onClick={fetchStatus}
          className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded"
          disabled={loading}
        >
          {loading ? 'Refreshing…' : 'Refresh Status'}
        </button>
      </div>
      <p className="text-sm text-gray-600 mb-2">
        CAPE-backed detonation test and status. If API HMAC auth is enabled, direct browser calls may be blocked.
      </p>
      {error && (
        <div className="text-red-600 text-sm mb-2">{error}</div>
      )}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <div className="text-xs uppercase text-gray-500">Gateway Running</div>
          <div className="text-base">{status?.running ? 'Yes' : 'No'}</div>
        </div>
        <div>
          <div className="text-xs uppercase text-gray-500">CAPE Enabled</div>
          <div className="text-base">{status?.cape_enabled ? 'Yes' : 'No'}</div>
        </div>
      </div>
      <div className="border-t pt-3">
        <label className="block text-sm font-medium mb-2">Upload a file to detonate</label>
        <input type="file" onChange={onFileChange} className="block w-full text-sm" />
        {detonateLoading && <div className="text-sm text-gray-600 mt-2">Submitting for detonation…</div>}
        {result && (
          <div className="mt-3 text-sm">
            <div><span className="font-semibold">Verdict:</span> {result.verdict}</div>
            <div><span className="font-semibold">Confidence:</span> {(result.confidence ?? 0).toFixed(2)}</div>
            <div><span className="font-semibold">Indicators:</span> {Array.isArray(result.threat_indicators) ? result.threat_indicators.join(', ') : ''}</div>
            <div><span className="font-semibold">Network Sampled:</span> {result.network_sampled}</div>
          </div>
        )}
      </div>
    </div>
  );
}


