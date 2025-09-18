import React, { useState, useEffect } from 'react';

const PerformanceMonitor = () => {
  const [performanceData, setPerformanceData] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [systemData, setSystemData] = useState(null);
  const [cacheData, setCacheData] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [autoRefresh, setAutoRefresh] = useState(false);

  useEffect(() => {
    fetchAllData();
    
    if (autoRefresh) {
      const interval = setInterval(fetchAllData, 30000); // Refresh every 30 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        fetchPerformanceStatus(),
        fetchHealthSummary(),
        fetchSystemPerformance(),
        fetchCachePerformance()
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchPerformanceStatus = async () => {
    try {
      const response = await fetch('/api/ui/performance/performance/status');
      if (!response.ok) throw new Error('Failed to fetch performance status');
      const data = await response.json();
      setPerformanceData(data);
    } catch (err) {
      console.error('Failed to fetch performance status:', err);
    }
  };

  const fetchHealthSummary = async () => {
    try {
      const response = await fetch('/api/ui/performance/health/summary');
      if (!response.ok) throw new Error('Failed to fetch health summary');
      const data = await response.json();
      setHealthData(data);
    } catch (err) {
      console.error('Failed to fetch health summary:', err);
    }
  };

  const fetchSystemPerformance = async () => {
    try {
      const response = await fetch('/api/ui/performance/performance/system');
      if (!response.ok) throw new Error('Failed to fetch system performance');
      const data = await response.json();
      setSystemData(data);
    } catch (err) {
      console.error('Failed to fetch system performance:', err);
    }
  };

  const fetchCachePerformance = async () => {
    try {
      const response = await fetch('/api/ui/performance/performance/cache');
      if (!response.ok) throw new Error('Failed to fetch cache performance');
      const data = await response.json();
      setCacheData(data);
    } catch (err) {
      console.error('Failed to fetch cache performance:', err);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const response = await fetch('/api/ui/performance/performance/audit-logs?limit=100');
      if (!response.ok) throw new Error('Failed to fetch audit logs');
      const data = await response.json();
      setAuditLogs(data.logs || []);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleOptimizeDatabase = async () => {
    try {
      const response = await fetch('/api/ui/performance/performance/database/optimize', {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to optimize database');
      const result = await response.json();
      alert(result.message);
      fetchAllData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleFlushCache = async (namespace = null) => {
    try {
      const url = namespace 
        ? `/api/ui/performance/performance/cache/flush?namespace=${namespace}`
        : '/api/ui/performance/performance/cache/flush';
      
      const response = await fetch(url, { method: 'POST' });
      if (!response.ok) throw new Error('Failed to flush cache');
      const result = await response.json();
      alert(result.message);
      fetchCachePerformance();
    } catch (err) {
      setError(err.message);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 bg-green-100';
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100';
      case 'critical':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const formatBytes = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading && !performanceData) {
    return <div className="p-4">Loading performance data...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Performance & System Monitoring</h3>
        <div className="flex gap-2">
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded ${autoRefresh ? 'bg-green-600 text-white' : 'bg-gray-300 text-gray-700'}`}
          >
            Auto Refresh {autoRefresh ? 'ON' : 'OFF'}
          </button>
          <button
            onClick={fetchAllData}
            className="px-4 py-2 bg-privik-blue-600 text-white rounded hover:bg-privik-blue-700"
          >
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Overall Status */}
      {performanceData && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-4">
            <span className={`px-3 py-1 rounded-full font-medium ${getStatusColor(performanceData.overall_status)}`}>
              {performanceData.overall_status.toUpperCase()}
            </span>
            <span className="text-sm text-gray-600">
              Last Updated: {new Date(performanceData.timestamp).toLocaleString()}
            </span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {['overview', 'system', 'cache', 'audit'].map((tab) => (
              <button
                key={tab}
                onClick={() => {
                  setActiveTab(tab);
                  if (tab === 'audit') fetchAuditLogs();
                }}
                className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                  activeTab === tab
                    ? 'border-privik-blue-500 text-privik-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Health Checks */}
          {healthData && healthData.results && (
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Health Checks</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(healthData.results).map(([checkName, result]) => (
                  <div key={checkName} className="p-4 border rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <h5 className="font-medium text-gray-900 capitalize">{checkName.replace('_', ' ')}</h5>
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(result.status)}`}>
                        {result.status}
                      </span>
                    </div>
                    {result.duration && (
                      <div className="text-sm text-gray-600">
                        Response: {result.duration.toFixed(3)}s
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* System Resources */}
          {systemData && (
            <div>
              <h4 className="font-medium text-gray-900 mb-3">System Resources</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* CPU */}
                <div className="p-4 border rounded-lg">
                  <h5 className="font-medium text-gray-900 mb-2">CPU Usage</h5>
                  <div className="text-2xl font-bold text-gray-900">
                    {systemData.cpu.usage_percent}%
                  </div>
                  <div className="text-sm text-gray-600">
                    {systemData.cpu.count} cores
                  </div>
                </div>

                {/* Memory */}
                <div className="p-4 border rounded-lg">
                  <h5 className="font-medium text-gray-900 mb-2">Memory Usage</h5>
                  <div className="text-2xl font-bold text-gray-900">
                    {systemData.memory.usage_percent}%
                  </div>
                  <div className="text-sm text-gray-600">
                    {systemData.memory.used_gb}GB / {systemData.memory.total_gb}GB
                  </div>
                </div>

                {/* Disk */}
                <div className="p-4 border rounded-lg">
                  <h5 className="font-medium text-gray-900 mb-2">Disk Usage</h5>
                  <div className="text-2xl font-bold text-gray-900">
                    {systemData.disk.usage_percent}%
                  </div>
                  <div className="text-sm text-gray-600">
                    {systemData.disk.used_gb}GB / {systemData.disk.total_gb}GB
                  </div>
                </div>

                {/* Process */}
                <div className="p-4 border rounded-lg">
                  <h5 className="font-medium text-gray-900 mb-2">Process Memory</h5>
                  <div className="text-2xl font-bold text-gray-900">
                    {systemData.process.memory_mb}MB
                  </div>
                  <div className="text-sm text-gray-600">
                    {systemData.process.num_threads} threads
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* System Tab */}
      {activeTab === 'system' && systemData && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* CPU Details */}
            <div className="p-4 border rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3">CPU Details</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Usage:</span>
                  <span className="font-medium">{systemData.cpu.usage_percent}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Cores:</span>
                  <span className="font-medium">{systemData.cpu.count}</span>
                </div>
              </div>
            </div>

            {/* Memory Details */}
            <div className="p-4 border rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3">Memory Details</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Total:</span>
                  <span className="font-medium">{systemData.memory.total_gb}GB</span>
                </div>
                <div className="flex justify-between">
                  <span>Used:</span>
                  <span className="font-medium">{systemData.memory.used_gb}GB</span>
                </div>
                <div className="flex justify-between">
                  <span>Available:</span>
                  <span className="font-medium">{systemData.memory.available_gb}GB</span>
                </div>
              </div>
            </div>

            {/* Disk Details */}
            <div className="p-4 border rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3">Disk Details</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Total:</span>
                  <span className="font-medium">{systemData.disk.total_gb}GB</span>
                </div>
                <div className="flex justify-between">
                  <span>Used:</span>
                  <span className="font-medium">{systemData.disk.used_gb}GB</span>
                </div>
                <div className="flex justify-between">
                  <span>Free:</span>
                  <span className="font-medium">{systemData.disk.free_gb}GB</span>
                </div>
              </div>
            </div>

            {/* Process Details */}
            <div className="p-4 border rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3">Process Details</h4>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span>Memory:</span>
                  <span className="font-medium">{systemData.process.memory_mb}MB</span>
                </div>
                <div className="flex justify-between">
                  <span>CPU:</span>
                  <span className="font-medium">{systemData.process.cpu_percent}%</span>
                </div>
                <div className="flex justify-between">
                  <span>Threads:</span>
                  <span className="font-medium">{systemData.process.num_threads}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Database Optimization */}
          <div className="p-4 border rounded-lg">
            <h4 className="font-medium text-gray-900 mb-3">Database Optimization</h4>
            <p className="text-sm text-gray-600 mb-3">
              Optimize database performance by creating indexes and analyzing queries.
            </p>
            <button
              onClick={handleOptimizeDatabase}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Optimize Database
            </button>
          </div>
        </div>
      )}

      {/* Cache Tab */}
      {activeTab === 'cache' && cacheData && (
        <div className="space-y-6">
          {/* Cache Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 border rounded-lg">
              <h5 className="font-medium text-gray-900 mb-2">Memory Usage</h5>
              <div className="text-2xl font-bold text-gray-900">
                {cacheData.used_memory || 'N/A'}
              </div>
            </div>
            <div className="p-4 border rounded-lg">
              <h5 className="font-medium text-gray-900 mb-2">Hit Rate</h5>
              <div className="text-2xl font-bold text-gray-900">
                {cacheData.hit_rate || 0}%
              </div>
            </div>
            <div className="p-4 border rounded-lg">
              <h5 className="font-medium text-gray-900 mb-2">Connected Clients</h5>
              <div className="text-2xl font-bold text-gray-900">
                {cacheData.connected_clients || 0}
              </div>
            </div>
          </div>

          {/* Cache Management */}
          <div className="p-4 border rounded-lg">
            <h4 className="font-medium text-gray-900 mb-3">Cache Management</h4>
            <div className="space-y-3">
              <div>
                <button
                  onClick={() => handleFlushCache()}
                  className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 mr-2"
                >
                  Flush All Cache
                </button>
                <button
                  onClick={() => handleFlushCache('email_analysis')}
                  className="px-4 py-2 bg-orange-600 text-white rounded hover:bg-orange-700 mr-2"
                >
                  Flush Email Analysis
                </button>
                <button
                  onClick={() => handleFlushCache('domain_reputation')}
                  className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-700"
                >
                  Flush Domain Reputation
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Audit Tab */}
      {activeTab === 'audit' && (
        <div className="space-y-6">
          <div className="p-4 border rounded-lg">
            <h4 className="font-medium text-gray-900 mb-3">Recent Audit Logs</h4>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {auditLogs.map((log) => (
                <div key={log.event_id} className="p-3 bg-gray-50 rounded text-sm">
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium">{log.event_type}</div>
                      <div className="text-gray-600">{log.description || log.event_title}</div>
                      {log.user_id && (
                        <div className="text-gray-500">User: {log.user_id}</div>
                      )}
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(log.timestamp).toLocaleString()}
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

export default PerformanceMonitor;
