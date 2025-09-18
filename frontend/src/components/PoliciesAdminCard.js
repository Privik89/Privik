import React, { useEffect, useState } from 'react';

export default function PoliciesAdminCard() {
  const [policies, setPolicies] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);

  const fetchPolicies = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/ui/policies');
      if (!res.ok) throw new Error(`Status ${res.status}`);
      const data = await res.json();
      setPolicies(data);
    } catch (e) {
      setError(`Failed to fetch policies: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchPolicies(); }, []);

  const updateThreshold = (key) => (e) => {
    setPolicies({
      ...policies,
      threat_thresholds: {
        ...policies.threat_thresholds,
        [key]: parseFloat(e.target.value)
      }
    });
  };

  const save = async () => {
    try {
      setSaving(true);
      setError(null);
      const res = await fetch('/api/ui/policies/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(policies),
      });
      if (!res.ok) throw new Error(`Status ${res.status}`);
    } catch (e) {
      setError(`Failed to save policies: ${e.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white shadow rounded p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold">Zero-Trust Policies</h3>
        <div className="flex gap-2">
          <button className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded" onClick={fetchPolicies} disabled={loading}>
            {loading ? 'Refreshing…' : 'Refresh'}
          </button>
          <button className="px-3 py-1 text-sm bg-privik-blue-600 text-white rounded" onClick={save} disabled={saving || !policies}>
            {saving ? 'Saving…' : 'Save'}
          </button>
        </div>
      </div>
      {error && <div className="text-red-600 text-sm mb-2">{error}</div>}
      {!policies && <div className="text-sm text-gray-600">Loading…</div>}
      {policies && (
        <div className="space-y-3">
          <div>
            <div className="text-xs uppercase text-gray-500 mb-1">Threat Thresholds</div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              {['sandbox', 'quarantine', 'block'].map((k) => (
                <div key={k}>
                  <label className="block text-xs text-gray-500 mb-1">{k}</label>
                  <input type="number" min="0" max="1" step="0.05" className="input-field" value={policies.threat_thresholds?.[k] ?? 0} onChange={updateThreshold(k)} />
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}


