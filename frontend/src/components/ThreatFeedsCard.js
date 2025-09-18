import React, { useState, useEffect } from 'react';

const ThreatFeedsCard = () => {
  const [feeds, setFeeds] = useState([]);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showRecords, setShowRecords] = useState(null);
  const [newFeed, setNewFeed] = useState({
    name: '',
    source_type: 'api',
    feed_url: '',
    api_key: '',
    category: 'malware',
    description: '',
    update_interval: 3600,
    confidence_threshold: 0.7
  });

  useEffect(() => {
    fetchFeeds();
    fetchStatus();
  }, []);

  const fetchFeeds = async () => {
    try {
      const response = await fetch('/api/ui/threat-feeds/feeds');
      if (!response.ok) throw new Error('Failed to fetch feeds');
      
      const data = await response.json();
      setFeeds(data.feeds || []);
    } catch (err) {
      setError(err.message);
    }
  };

  const fetchStatus = async () => {
    try {
      const response = await fetch('/api/ui/threat-feeds/feeds/status');
      if (!response.ok) throw new Error('Failed to fetch status');
      
      const data = await response.json();
      setStatus(data);
    } catch (err) {
      console.error('Failed to fetch status:', err);
    }
  };

  const createFeed = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch('/api/ui/threat-feeds/feeds', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newFeed)
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create feed');
      }
      
      setNewFeed({
        name: '',
        source_type: 'api',
        feed_url: '',
        api_key: '',
        category: 'malware',
        description: '',
        update_interval: 3600,
        confidence_threshold: 0.7
      });
      setShowCreateForm(false);
      fetchFeeds();
      fetchStatus();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const deleteFeed = async (feedId, feedName) => {
    if (!confirm(`Are you sure you want to delete the feed "${feedName}"?`)) return;
    
    try {
      const response = await fetch(`/api/ui/threat-feeds/feeds/${feedId}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error('Failed to delete feed');
      
      fetchFeeds();
      fetchStatus();
    } catch (err) {
      setError(err.message);
    }
  };

  const updateFeed = async (feedId) => {
    try {
      const response = await fetch(`/api/ui/threat-feeds/feeds/${feedId}/update`, {
        method: 'POST'
      });
      
      if (!response.ok) throw new Error('Failed to update feed');
      
      fetchFeeds();
    } catch (err) {
      setError(err.message);
    }
  };

  const fetchFeedRecords = async (feedId) => {
    try {
      const response = await fetch(`/api/ui/threat-feeds/feeds/${feedId}/records?limit=50`);
      if (!response.ok) throw new Error('Failed to fetch records');
      
      const data = await response.json();
      setShowRecords({ feedId, records: data.records });
    } catch (err) {
      setError(err.message);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'active':
        return 'text-green-600 bg-green-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      case 'paused':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getCategoryColor = (category) => {
    switch (category) {
      case 'malware':
        return 'text-red-600 bg-red-100';
      case 'phishing':
        return 'text-orange-600 bg-orange-100';
      case 'botnet':
        return 'text-purple-600 bg-purple-100';
      case 'custom':
        return 'text-blue-600 bg-blue-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading && feeds.length === 0) {
    return <div className="p-4">Loading threat feeds...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Threat Intelligence Feeds</h3>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="px-4 py-2 bg-privik-blue-600 text-white rounded hover:bg-privik-blue-700"
        >
          Add Feed
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Status Overview */}
      {status && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-3">Feed Status Overview</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{status.total_feeds}</div>
              <div className="text-sm text-gray-600">Total Feeds</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{status.active_feeds}</div>
              <div className="text-sm text-gray-600">Active</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{status.error_feeds}</div>
              <div className="text-sm text-gray-600">Errors</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">{status.total_records}</div>
              <div className="text-sm text-gray-600">Total Records</div>
            </div>
          </div>
        </div>
      )}

      {/* Create Feed Form */}
      {showCreateForm && (
        <form onSubmit={createFeed} className="mb-6 p-4 border border-gray-200 rounded-lg">
          <h4 className="text-md font-medium mb-3">Create New Threat Feed</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                value={newFeed.name}
                onChange={(e) => setNewFeed({...newFeed, name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Source Type</label>
              <select
                value={newFeed.source_type}
                onChange={(e) => setNewFeed({...newFeed, source_type: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="api">API</option>
                <option value="webhook">Webhook</option>
                <option value="file">File</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Feed URL</label>
              <input
                type="url"
                value={newFeed.feed_url}
                onChange={(e) => setNewFeed({...newFeed, feed_url: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
              <input
                type="password"
                value={newFeed.api_key}
                onChange={(e) => setNewFeed({...newFeed, api_key: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
              <select
                value={newFeed.category}
                onChange={(e) => setNewFeed({...newFeed, category: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="malware">Malware</option>
                <option value="phishing">Phishing</option>
                <option value="botnet">Botnet</option>
                <option value="custom">Custom</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Update Interval (seconds)</label>
              <input
                type="number"
                value={newFeed.update_interval}
                onChange={(e) => setNewFeed({...newFeed, update_interval: parseInt(e.target.value)})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={newFeed.description}
              onChange={(e) => setNewFeed({...newFeed, description: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
              rows="2"
            />
          </div>
          <div className="mt-4 flex gap-2">
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-privik-blue-600 text-white rounded hover:bg-privik-blue-700 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Feed'}
            </button>
            <button
              type="button"
              onClick={() => setShowCreateForm(false)}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Feeds List */}
      <div className="space-y-4">
        {feeds.map((feed) => (
          <div key={feed.id} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3">
                <h5 className="font-medium text-gray-900">{feed.name}</h5>
                <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(feed.status)}`}>
                  {feed.status}
                </span>
                <span className={`px-2 py-1 text-xs rounded-full ${getCategoryColor(feed.category)}`}>
                  {feed.category}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => updateFeed(feed.id)}
                  className="text-sm text-privik-blue-600 hover:text-privik-blue-800"
                >
                  Update
                </button>
                <button
                  onClick={() => fetchFeedRecords(feed.id)}
                  className="text-sm text-privik-blue-600 hover:text-privik-blue-800"
                >
                  Records
                </button>
                <button
                  onClick={() => deleteFeed(feed.id, feed.name)}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  Delete
                </button>
              </div>
            </div>
            
            <div className="text-sm text-gray-600 mb-2">
              {feed.description}
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <span className="font-medium">Records:</span> {feed.total_records}
              </div>
              <div>
                <span className="font-medium">Last Updated:</span> {feed.last_updated ? new Date(feed.last_updated).toLocaleString() : 'Never'}
              </div>
              <div>
                <span className="font-medium">Next Update:</span> {feed.next_update ? new Date(feed.next_update).toLocaleString() : 'N/A'}
              </div>
              <div>
                <span className="font-medium">Errors:</span> {feed.error_count}
              </div>
            </div>
          </div>
        ))}
      </div>

      {feeds.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No threat feeds configured. Add your first feed to get started.
        </div>
      )}

      {/* Records Modal */}
      {showRecords && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-96 overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h4 className="text-lg font-semibold">Feed Records</h4>
              <button
                onClick={() => setShowRecords(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-2">
              {showRecords.records.map((record) => (
                <div key={record.id} className="flex items-center justify-between p-2 border rounded">
                  <div>
                    <div className="font-medium">{record.indicator}</div>
                    <div className="text-sm text-gray-600">
                      {record.indicator_type} • {record.threat_type} • {record.severity}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm font-medium">
                      {Math.round(record.confidence * 100)}%
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(record.last_seen).toLocaleDateString()}
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

export default ThreatFeedsCard;
