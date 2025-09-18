import React, { useEffect, useState } from 'react';
import ArtifactPreview from '../components/ArtifactPreview';

export default function Incidents() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);

  const fetchList = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/soc/incidents');
      if (!res.ok) throw new Error(`Status ${res.status}`);
      const data = await res.json();
      setItems(data);
    } catch (e) {
      setError(`Failed to load incidents: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const fetchDetail = async (id) => {
    try {
      setError(null);
      setDetail(null);
      const res = await fetch(`/api/soc/incidents/${id}`);
      if (!res.ok) throw new Error(`Status ${res.status}`);
      const data = await res.json();
      setDetail(data);
    } catch (e) {
      setError(`Failed to load detail: ${e.message}`);
    }
  };

  useEffect(() => { fetchList(); }, []);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Incidents</h1>
        <button onClick={fetchList} className="btn-primary">Refresh</button>
      </div>
      {error && <div className="text-sm text-red-600">{error}</div>}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1">
          <div className="bg-white rounded shadow">
            <div className="p-3 border-b font-semibold">Recent Incidents</div>
            <ul className="divide-y">
              {loading && <li className="p-3 text-sm text-gray-600">Loading…</li>}
              {!loading && items.map((it) => (
                <li key={it.id} className={`p-3 text-sm cursor-pointer hover:bg-gray-50 ${selected === it.id ? 'bg-privik-blue-50' : ''}`} onClick={() => { setSelected(it.id); fetchDetail(it.id); }}>
                  <div className="flex justify-between">
                    <div className="font-medium">{it.attachment_filename || it.email_subject || `Incident #${it.id}`}</div>
                    <div className={`text-xs ${it.verdict === 'malicious' ? 'text-red-600' : it.verdict === 'suspicious' ? 'text-amber-600' : 'text-green-600'}`}>{it.verdict || 'unknown'}</div>
                  </div>
                  <div className="text-xs text-gray-500">{new Date(it.created_at).toLocaleString()}</div>
                </li>
              ))}
            </ul>
          </div>
        </div>
        <div className="md:col-span-2">
          <div className="bg-white rounded shadow p-4 min-h-[300px]">
            {!detail && <div className="text-sm text-gray-600">Select an incident to view details.</div>}
            {detail && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-lg font-semibold">{detail.file?.filename || 'Attachment'}</div>
                    <div className="text-sm text-gray-500">{detail.email?.subject || ''}</div>
                  </div>
                  <div className="text-right">
                    <div className={`text-sm font-medium ${detail.verdict === 'malicious' ? 'text-red-600' : detail.verdict === 'suspicious' ? 'text-amber-600' : 'text-green-600'}`}>{detail.verdict}</div>
                    <div className="text-xs text-gray-500">Confidence: {(detail.confidence ?? 0).toFixed(2)}</div>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs uppercase text-gray-500 mb-1">Behavior</div>
                    <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-48">{JSON.stringify(detail.behavior, null, 2)}</pre>
                  </div>
                  <div>
                    <div className="text-xs uppercase text-gray-500 mb-1">AI</div>
                    <pre className="text-xs bg-gray-50 p-2 rounded overflow-auto max-h-48">{JSON.stringify(detail.ai, null, 2)}</pre>
                    {detail.ai?.details?.virustotal && (
                      <div className="mt-2 text-xs">
                        <div className="font-semibold">VirusTotal</div>
                        <div>Malicious: {detail.ai.details.virustotal.malicious} Suspicious: {detail.ai.details.virustotal.suspicious} Undetected: {detail.ai.details.virustotal.undetected}</div>
                      </div>
                    )}
                  </div>
                </div>
                <div>
                  <div className="text-xs uppercase text-gray-500 mb-1">Artifacts</div>
                  <div className="text-xs text-gray-600 mb-2">
                    Report: {detail.artifacts?.report_key ? (
                      <a className="text-privik-blue-600 underline" href={`/api/ui/artifacts/get?key=${encodeURIComponent(detail.artifacts.report_key)}`} target="_blank" rel="noreferrer">download</a>
                    ) : 'n/a'}
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {(detail.artifacts?.screenshots || []).map((k) => (
                      <a key={k} href={`/api/ui/artifacts/get?key=${encodeURIComponent(k)}`} target="_blank" rel="noreferrer">
                        <img alt="screenshot" className="w-full h-24 object-cover rounded border" src={`/api/ui/artifacts/get?key=${encodeURIComponent(k)}`} />
                      </a>
                    ))}
                  </div>
                  <div className="mt-3">
                    <a className="text-sm text-gray-700 underline" href={`/api/ui/soc/incidents/${selected}/export.json`} target="_blank" rel="noreferrer">Export JSON</a>
                  </div>
                  
                  {/* Link Analysis Artifacts */}
                  {detail.execution_logs && detail.execution_logs.some(log => log.type === 'link_analysis' && log.artifacts) && (
                    <div className="mt-6">
                      <h4 className="text-sm font-medium text-gray-900 mb-3">Link Analysis Artifacts</h4>
                      <div className="space-y-3">
                        {detail.execution_logs
                          .filter(log => log.type === 'link_analysis' && log.artifacts)
                          .map((log, index) => (
                            <div key={index}>
                              {log.artifacts.console_logs && (
                                <ArtifactPreview 
                                  artifactKey={log.artifacts.console_logs} 
                                  artifactType="console" 
                                />
                              )}
                              {log.artifacts.dom_snapshot && (
                                <ArtifactPreview 
                                  artifactKey={log.artifacts.dom_snapshot} 
                                  artifactType="dom" 
                                />
                              )}
                              {log.artifacts.har_data && (
                                <ArtifactPreview 
                                  artifactKey={log.artifacts.har_data} 
                                  artifactType="har" 
                                />
                              )}
                            </div>
                          ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}


