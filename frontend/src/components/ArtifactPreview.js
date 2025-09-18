import React, { useState, useEffect } from 'react';

const ArtifactPreview = ({ artifactKey, artifactType }) => {
  const [content, setContent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    if (artifactKey) {
      fetchArtifact();
    }
  }, [artifactKey]);

  const fetchArtifact = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/ui/artifacts/get?key=${encodeURIComponent(artifactKey)}`);
      if (!response.ok) throw new Error('Failed to fetch artifact');
      
      if (artifactType === 'json') {
        const text = await response.text();
        setContent(JSON.parse(text));
      } else {
        const text = await response.text();
        setContent(text);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getArtifactIcon = () => {
    switch (artifactType) {
      case 'console':
        return '🖥️';
      case 'dom':
        return '📄';
      case 'har':
        return '🌐';
      default:
        return '📁';
    }
  };

  const getArtifactTitle = () => {
    switch (artifactType) {
      case 'console':
        return 'Console Logs';
      case 'dom':
        return 'DOM Snapshot';
      case 'har':
        return 'Network Activity (HAR)';
      default:
        return 'Artifact';
    }
  };

  const renderConsoleLogs = (logs) => {
    if (!Array.isArray(logs)) return <pre>{JSON.stringify(logs, null, 2)}</pre>;
    
    return (
      <div className="space-y-2">
        {logs.map((log, index) => (
          <div key={index} className={`p-2 rounded text-sm ${
            log.type === 'error' ? 'bg-red-100 text-red-800' :
            log.type === 'warn' ? 'bg-yellow-100 text-yellow-800' :
            log.type === 'info' ? 'bg-blue-100 text-blue-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            <div className="flex justify-between items-start">
              <span className="font-medium">{log.type.toUpperCase()}</span>
              <span className="text-xs text-gray-500">{log.timestamp}</span>
            </div>
            <div className="mt-1 font-mono text-xs">{log.text}</div>
          </div>
        ))}
      </div>
    );
  };

  const renderHARData = (har) => {
    if (!har) return <div>No HAR data available</div>;
    
    return (
      <div className="space-y-4">
        <div className="bg-gray-50 p-3 rounded">
          <h4 className="font-medium text-sm mb-2">Navigation Timing</h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>DNS Lookup: {har.domainLookupEnd - har.domainLookupStart}ms</div>
            <div>TCP Connect: {har.connectEnd - har.connectStart}ms</div>
            <div>Request: {har.responseStart - har.requestStart}ms</div>
            <div>Response: {har.responseEnd - har.responseStart}ms</div>
          </div>
        </div>
        <details>
          <summary className="cursor-pointer font-medium text-sm">Full HAR Data</summary>
          <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto max-h-64">
            {JSON.stringify(har, null, 2)}
          </pre>
        </details>
      </div>
    );
  };

  const renderDOMSnapshot = (dom) => {
    if (!dom) return <div>No DOM data available</div>;
    
    return (
      <div>
        <div className="mb-2 text-sm text-gray-600">
          DOM Size: {dom.length} characters
        </div>
        <details>
          <summary className="cursor-pointer font-medium text-sm">View DOM</summary>
          <div className="mt-2 max-h-64 overflow-auto">
            <pre className="text-xs bg-gray-100 p-2 rounded">
              {dom.substring(0, 2000)}{dom.length > 2000 ? '...' : ''}
            </pre>
          </div>
        </details>
      </div>
    );
  };

  const renderContent = () => {
    if (loading) return <div className="text-sm text-gray-500">Loading...</div>;
    if (error) return <div className="text-sm text-red-500">Error: {error}</div>;
    if (!content) return <div className="text-sm text-gray-500">No content</div>;

    switch (artifactType) {
      case 'console':
        return renderConsoleLogs(content);
      case 'har':
        return renderHARData(content);
      case 'dom':
        return renderDOMSnapshot(content);
      default:
        return <pre className="text-xs bg-gray-100 p-2 rounded overflow-auto max-h-64">
          {JSON.stringify(content, null, 2)}
        </pre>;
    }
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-lg">{getArtifactIcon()}</span>
          <h4 className="font-medium text-sm">{getArtifactTitle()}</h4>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-privik-blue-600 hover:text-privik-blue-800"
          >
            {expanded ? 'Collapse' : 'Expand'}
          </button>
          <a
            href={`/api/ui/artifacts/get?key=${encodeURIComponent(artifactKey)}`}
            target="_blank"
            rel="noreferrer"
            className="text-xs text-privik-blue-600 hover:text-privik-blue-800"
          >
            Download
          </a>
        </div>
      </div>
      
      {expanded && (
        <div className="border-t pt-3">
          {renderContent()}
        </div>
      )}
    </div>
  );
};

export default ArtifactPreview;
