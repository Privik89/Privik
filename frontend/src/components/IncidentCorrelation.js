import React, { useState, useEffect } from 'react';

const IncidentCorrelation = () => {
  const [incidents, setIncidents] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [selectedIncident, setSelectedIncident] = useState(null);
  const [timeline, setTimeline] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({
    incident_type: '',
    severity: '',
    status: ''
  });
  const [pagination, setPagination] = useState({
    limit: 50,
    offset: 0,
    total: 0
  });

  useEffect(() => {
    fetchIncidents();
    fetchStatistics();
  }, [filters, pagination.offset]);

  const fetchIncidents = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.incident_type) params.append('incident_type', filters.incident_type);
      if (filters.severity) params.append('severity', filters.severity);
      if (filters.status) params.append('status', filters.status);
      params.append('limit', pagination.limit);
      params.append('offset', pagination.offset);
      
      const response = await fetch(`/api/ui/incident-correlation/incidents?${params}`);
      if (!response.ok) throw new Error('Failed to fetch incidents');
      
      const data = await response.json();
      setIncidents(data.incidents || []);
      setPagination(prev => ({ ...prev, total: data.total_count }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await fetch('/api/ui/incident-correlation/incidents/statistics');
      if (!response.ok) throw new Error('Failed to fetch statistics');
      
      const data = await response.json();
      setStatistics(data);
    } catch (err) {
      console.error('Failed to fetch statistics:', err);
    }
  };

  const fetchIncidentDetails = async (incidentId) => {
    try {
      const response = await fetch(`/api/ui/incident-correlation/incidents/${incidentId}`);
      if (!response.ok) throw new Error('Failed to fetch incident details');
      
      const data = await response.json();
      setSelectedIncident(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const fetchTimeline = async (incidentId) => {
    try {
      const response = await fetch(`/api/ui/incident-correlation/incidents/${incidentId}/timeline`);
      if (!response.ok) throw new Error('Failed to fetch timeline');
      
      const data = await response.json();
      setTimeline(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleIncidentAction = async (incidentId, action, data = {}) => {
    try {
      let endpoint, method, body;
      
      switch (action) {
        case 'assign':
          endpoint = `/api/ui/incident-correlation/incidents/${incidentId}/assign`;
          method = 'POST';
          body = JSON.stringify({ assigned_to: data.assigned_to });
          break;
        case 'resolve':
          endpoint = `/api/ui/incident-correlation/incidents/${incidentId}/resolve`;
          method = 'POST';
          body = JSON.stringify({ 
            resolved_by: data.resolved_by,
            resolution_notes: data.resolution_notes
          });
          break;
        default:
          throw new Error('Unknown action');
      }
      
      const response = await fetch(endpoint, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Failed to ${action} incident`);
      }
      
      const result = await response.json();
      alert(result.message);
      
      // Refresh data
      fetchIncidents();
      if (selectedIncident && selectedIncident.incident.incident_id === incidentId) {
        fetchIncidentDetails(incidentId);
      }
      
    } catch (err) {
      setError(err.message);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
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

  const getStatusColor = (status) => {
    switch (status) {
      case 'open':
        return 'text-red-600 bg-red-100';
      case 'investigating':
        return 'text-orange-600 bg-orange-100';
      case 'resolved':
        return 'text-green-600 bg-green-100';
      case 'false_positive':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getIncidentTypeColor = (type) => {
    switch (type) {
      case 'phishing':
        return 'text-blue-600 bg-blue-100';
      case 'malware':
        return 'text-red-600 bg-red-100';
      case 'bec':
        return 'text-purple-600 bg-purple-100';
      case 'suspicious':
        return 'text-yellow-600 bg-yellow-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading && incidents.length === 0) {
    return <div className="p-4">Loading incidents...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Incident Correlation & Timeline</h3>
        <div className="flex gap-2">
          <button
            onClick={fetchIncidents}
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

      {/* Statistics Overview */}
      {statistics && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-3">Incident Statistics</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{statistics.total_incidents}</div>
              <div className="text-sm text-gray-600">Total Incidents</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{statistics.open_incidents}</div>
              <div className="text-sm text-gray-600">Open Incidents</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{statistics.recent_incidents}</div>
              <div className="text-sm text-gray-600">Recent (24h)</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{statistics.type_statistics?.phishing || 0}</div>
              <div className="text-sm text-gray-600">Phishing</div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="mb-4 flex gap-4">
        <select
          value={filters.incident_type}
          onChange={(e) => setFilters({...filters, incident_type: e.target.value})}
          className="px-3 py-2 border border-gray-300 rounded-md"
        >
          <option value="">All Types</option>
          <option value="phishing">Phishing</option>
          <option value="malware">Malware</option>
          <option value="bec">BEC</option>
          <option value="suspicious">Suspicious</option>
        </select>
        
        <select
          value={filters.severity}
          onChange={(e) => setFilters({...filters, severity: e.target.value})}
          className="px-3 py-2 border border-gray-300 rounded-md"
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        
        <select
          value={filters.status}
          onChange={(e) => setFilters({...filters, status: e.target.value})}
          className="px-3 py-2 border border-gray-300 rounded-md"
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="investigating">Investigating</option>
          <option value="resolved">Resolved</option>
          <option value="false_positive">False Positive</option>
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Incidents List */}
        <div>
          <h4 className="font-medium text-gray-900 mb-3">Security Incidents</h4>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {incidents.map((incident) => (
              <div
                key={incident.id}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedIncident?.incident.incident_id === incident.incident_id
                    ? 'border-privik-blue-500 bg-privik-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
                onClick={() => {
                  fetchIncidentDetails(incident.incident_id);
                  fetchTimeline(incident.incident_id);
                }}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex gap-2">
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getIncidentTypeColor(incident.incident_type)}`}>
                      {incident.incident_type}
                    </span>
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getSeverityColor(incident.severity)}`}>
                      {incident.severity}
                    </span>
                    <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(incident.status)}`}>
                      {incident.status}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500">
                    {Math.round(incident.confidence_score * 100)}%
                  </div>
                </div>
                
                <h5 className="font-medium text-gray-900 mb-1">{incident.title}</h5>
                <p className="text-sm text-gray-600 mb-2">{incident.description}</p>
                
                <div className="flex justify-between items-center text-xs text-gray-500">
                  <span>ID: {incident.incident_id}</span>
                  <span>{incident.email_count} emails</span>
                  <span>{new Date(incident.first_seen).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {pagination.total > pagination.limit && (
            <div className="mt-4 flex justify-between items-center">
              <div className="text-sm text-gray-700">
                Showing {pagination.offset + 1} to {Math.min(pagination.offset + pagination.limit, pagination.total)} of {pagination.total} incidents
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setPagination(prev => ({ ...prev, offset: Math.max(0, prev.offset - prev.limit) }))}
                  disabled={pagination.offset === 0}
                  className="px-3 py-1 bg-gray-300 text-gray-700 rounded disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPagination(prev => ({ ...prev, offset: prev.offset + prev.limit }))}
                  disabled={pagination.offset + pagination.limit >= pagination.total}
                  className="px-3 py-1 bg-gray-300 text-gray-700 rounded disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Incident Details & Timeline */}
        <div>
          {selectedIncident ? (
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Incident Details</h4>
              <div className="space-y-4">
                {/* Incident Info */}
                <div className="p-4 border rounded-lg">
                  <div className="flex justify-between items-start mb-3">
                    <h5 className="font-medium text-gray-900">{selectedIncident.incident.title}</h5>
                    <div className="flex gap-2">
                      {selectedIncident.incident.status === 'open' && (
                        <>
                          <button
                            onClick={() => {
                              const assigned_to = prompt('Assign to:');
                              if (assigned_to) {
                                handleIncidentAction(selectedIncident.incident.incident_id, 'assign', { assigned_to });
                              }
                            }}
                            className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                          >
                            Assign
                          </button>
                          <button
                            onClick={() => {
                              const resolved_by = prompt('Resolved by:');
                              const resolution_notes = prompt('Resolution notes:');
                              if (resolved_by) {
                                handleIncidentAction(selectedIncident.incident.incident_id, 'resolve', { resolved_by, resolution_notes });
                              }
                            }}
                            className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                          >
                            Resolve
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Type:</span> {selectedIncident.incident.incident_type}
                    </div>
                    <div>
                      <span className="font-medium">Severity:</span> {selectedIncident.incident.severity}
                    </div>
                    <div>
                      <span className="font-medium">Status:</span> {selectedIncident.incident.status}
                    </div>
                    <div>
                      <span className="font-medium">Confidence:</span> {Math.round(selectedIncident.incident.confidence_score * 100)}%
                    </div>
                  </div>
                  
                  <div className="mt-3 text-sm text-gray-600">
                    <p>{selectedIncident.incident.description}</p>
                  </div>
                </div>

                {/* Related Emails */}
                {selectedIncident.emails && selectedIncident.emails.length > 0 && (
                  <div className="p-4 border rounded-lg">
                    <h5 className="font-medium text-gray-900 mb-3">Related Emails ({selectedIncident.emails.length})</h5>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {selectedIncident.emails.map((email) => (
                        <div key={email.id} className="p-2 bg-gray-50 rounded text-sm">
                          <div className="font-medium">{email.subject}</div>
                          <div className="text-gray-600">From: {email.sender}</div>
                          <div className="text-gray-500">Score: {Math.round(email.threat_score * 100)}%</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Correlations */}
                {selectedIncident.correlations && selectedIncident.correlations.length > 0 && (
                  <div className="p-4 border rounded-lg">
                    <h5 className="font-medium text-gray-900 mb-3">Correlations ({selectedIncident.correlations.length})</h5>
                    <div className="space-y-2 max-h-40 overflow-y-auto">
                      {selectedIncident.correlations.map((correlation) => (
                        <div key={correlation.id} className="p-2 bg-gray-50 rounded text-sm">
                          <div className="font-medium">{correlation.correlation_type}</div>
                          <div className="text-gray-600">{correlation.correlation_value}</div>
                          <div className="text-gray-500">Confidence: {Math.round(correlation.correlation_confidence * 100)}%</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              Select an incident to view details
            </div>
          )}
        </div>
      </div>

      {/* Timeline Modal */}
      {timeline && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-96 overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h4 className="text-lg font-semibold">Timeline: {timeline.incident.title}</h4>
              <button
                onClick={() => setTimeline(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <div className="space-y-4">
              {timeline.timeline_events.map((event, index) => (
                <div key={event.id} className="flex items-start space-x-3">
                  <div className="flex-shrink-0 w-2 h-2 bg-privik-blue-600 rounded-full mt-2"></div>
                  <div className="flex-1">
                    <div className="flex justify-between items-start">
                      <h5 className="font-medium text-gray-900">{event.title}</h5>
                      <span className="text-sm text-gray-500">
                        {new Date(event.event_time).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                    <div className="text-xs text-gray-500 mt-1">
                      Source: {event.event_source} | Type: {event.event_type}
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

export default IncidentCorrelation;
