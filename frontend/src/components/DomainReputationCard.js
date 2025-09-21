import React, { useState } from 'react';

const DomainReputationCard = () => {
  const [domain, setDomain] = useState('');
  const [score, setScore] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  const fetchDomainScore = async (domainToCheck, forceRefresh = false) => {
    if (!domainToCheck) return;
    
    try {
      setLoading(true);
      setError(null);
      
      const params = new URLSearchParams();
      if (forceRefresh) {
        params.append('force_refresh', 'true');
      }
      
      const response = await fetch(`/api/ui/domain-reputation/domains/${encodeURIComponent(domainToCheck)}/score?${params}`);
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Domain score not available');
        }
        throw new Error('Failed to fetch domain score');
      }
      
      const data = await response.json();
      setScore(data);
    } catch (err) {
      setError(err.message);
      setScore(null);
    } finally {
      setLoading(false);
    }
  };

  const fetchDomainHistory = async (domainToCheck) => {
    if (!domainToCheck) return;
    
    try {
      const response = await fetch(`/api/ui/domain-reputation/domains/${encodeURIComponent(domainToCheck)}/history`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch domain history');
      }
      
      const data = await response.json();
      setHistory(data.scores || []);
      setShowHistory(true);
    } catch (err) {
      setError(err.message);
    }
  };

  const refreshDomainScore = async () => {
    if (domain) {
      await fetchDomainScore(domain, true);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchDomainScore(domain);
  };

  const getRiskLevelColor = (riskLevel) => {
    switch (riskLevel) {
      case 'critical':
        return 'text-red-600 bg-red-100';
      case 'high':
        return 'text-orange-600 bg-orange-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'low':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getScoreColor = (score) => {
    if (score <= 0.2) return 'text-red-600';
    if (score <= 0.4) return 'text-orange-600';
    if (score <= 0.6) return 'text-yellow-600';
    return 'text-green-600';
  };

  const formatConfidence = (confidence) => {
    return `${Math.round(confidence * 100)}%`;
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Domain Reputation Checker</h3>
      </div>

      <form onSubmit={handleSubmit} className="mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            placeholder="Enter domain (e.g., example.com)"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-privik-blue-500"
          />
          <button
            type="submit"
            disabled={loading || !domain}
            className="px-4 py-2 bg-privik-blue-600 text-white rounded hover:bg-privik-blue-700 disabled:opacity-50"
          >
            {loading ? 'Checking...' : 'Check'}
          </button>
        </div>
      </form>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {score && (
        <div className="space-y-4">
          {/* Main Score Display */}
          <div className="bg-gray-50 p-4 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium text-gray-900">Domain: {score.domain}</h4>
              <div className="flex gap-2">
                <button
                  onClick={refreshDomainScore}
                  className="text-sm text-privik-blue-600 hover:text-privik-blue-800"
                >
                  Refresh
                </button>
                <button
                  onClick={() => fetchDomainHistory(domain)}
                  className="text-sm text-privik-blue-600 hover:text-privik-blue-800"
                >
                  History
                </button>
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              <div className="text-center">
                <div className={`text-2xl font-bold ${getScoreColor(score.reputation_score)}`}>
                  {Math.round(score.reputation_score * 100)}
                </div>
                <div className="text-sm text-gray-600">Reputation Score</div>
              </div>
              <div className="text-center">
                <div className={`text-lg font-semibold px-2 py-1 rounded-full ${getRiskLevelColor(score.risk_level)}`}>
                  {score.risk_level.toUpperCase()}
                </div>
                <div className="text-sm text-gray-600">Risk Level</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-semibold text-gray-900">
                  {formatConfidence(score.confidence)}
                </div>
                <div className="text-sm text-gray-600">Confidence</div>
              </div>
            </div>
          </div>

          {/* Threat Indicators */}
          {score.threat_indicators && score.threat_indicators.length > 0 && (
            <div>
              <h5 className="font-medium text-gray-900 mb-2">Threat Indicators</h5>
              <div className="flex flex-wrap gap-2">
                {score.threat_indicators.map((indicator, index) => (
                  <span
                    key={index}
                    className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full"
                  >
                    {indicator.replace('_', ' ')}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Source Scores */}
          {score.sources && score.sources.length > 0 && (
            <div>
              <h5 className="font-medium text-gray-900 mb-2">Source Scores</h5>
              <div className="space-y-2">
                {score.sources.map((source, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div className="flex items-center gap-2">
                      <span className="font-medium capitalize">{source.source.replace('_', ' ')}</span>
                      {source.threat_indicators && source.threat_indicators.length > 0 && (
                        <span className="text-xs text-red-600">({source.threat_indicators.length} threats)</span>
                      )}
                    </div>
                    <div className="flex items-center gap-4">
                      <span className={`font-semibold ${getScoreColor(source.score)}`}>
                        {Math.round(source.score * 100)}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatConfidence(source.confidence)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Last Updated */}
          <div className="text-xs text-gray-500">
            Last updated: {new Date(score.last_updated).toLocaleString()}
          </div>
        </div>
      )}

      {/* History Modal */}
      {showHistory && history.length > 0 && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-96 overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h4 className="text-lg font-semibold">Domain History: {domain}</h4>
              <button
                onClick={() => setShowHistory(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-2">
              {history.map((entry, index) => (
                <div key={index} className="flex items-center justify-between p-2 border rounded">
                  <div>
                    <div className="font-medium">{new Date(entry.last_updated).toLocaleString()}</div>
                    <div className="text-sm text-gray-600">
                      Risk: <span className={getRiskLevelColor(entry.risk_level)}>{entry.risk_level}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={`font-bold ${getScoreColor(entry.reputation_score)}`}>
                      {Math.round(entry.reputation_score * 100)}
                    </div>
                    <div className="text-xs text-gray-500">
                      {formatConfidence(entry.confidence)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DomainReputationCard;
