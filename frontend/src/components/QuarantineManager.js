import React, { useState, useEffect } from 'react';

const QuarantineManager = () => {
  const [emails, setEmails] = useState([]);
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedEmails, setSelectedEmails] = useState([]);
  const [showBulkActions, setShowBulkActions] = useState(false);
  const [showEmailDetail, setShowEmailDetail] = useState(null);
  const [filters, setFilters] = useState({
    status: '',
    reason: ''
  });
  const [pagination, setPagination] = useState({
    limit: 50,
    offset: 0,
    total: 0
  });

  useEffect(() => {
    fetchEmails();
    fetchStatistics();
  }, [filters, pagination.offset]);

  const fetchEmails = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.reason) params.append('reason', filters.reason);
      params.append('limit', pagination.limit);
      params.append('offset', pagination.offset);
      
      const response = await fetch(`/api/ui/quarantine/quarantine?${params}`);
      if (!response.ok) throw new Error('Failed to fetch quarantined emails');
      
      const data = await response.json();
      setEmails(data.emails || []);
      setPagination(prev => ({ ...prev, total: data.total_count }));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await fetch('/api/ui/quarantine/quarantine/statistics');
      if (!response.ok) throw new Error('Failed to fetch statistics');
      
      const data = await response.json();
      setStatistics(data);
    } catch (err) {
      console.error('Failed to fetch statistics:', err);
    }
  };

  const fetchEmailDetail = async (quarantineId) => {
    try {
      const response = await fetch(`/api/ui/quarantine/quarantine/${quarantineId}`);
      if (!response.ok) throw new Error('Failed to fetch email details');
      
      const data = await response.json();
      setShowEmailDetail(data);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleQuarantineAction = async (quarantineId, action, reason = '') => {
    try {
      const endpoint = `/api/ui/quarantine/quarantine/${quarantineId}/${action}`;
      const response = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          [`${action}d_by`]: 'admin',
          [`${action}_reason`]: reason
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Failed to ${action} email`);
      }
      
      const result = await response.json();
      alert(result.message);
      
      // Refresh data
      fetchEmails();
      fetchStatistics();
      setShowEmailDetail(null);
      
    } catch (err) {
      setError(err.message);
    }
  };

  const handleBulkAction = async (action, reason = '') => {
    if (selectedEmails.length === 0) {
      alert('Please select emails to perform bulk action');
      return;
    }
    
    if (!confirm(`Are you sure you want to ${action} ${selectedEmails.length} emails?`)) {
      return;
    }
    
    try {
      const response = await fetch('/api/ui/quarantine/quarantine/bulk-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quarantine_ids: selectedEmails,
          action: action,
          performed_by: 'admin',
          action_reason: reason
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || `Failed to perform bulk ${action}`);
      }
      
      const result = await response.json();
      alert(`Bulk ${action} completed: ${result.successful_actions} successful, ${result.failed_actions} failed`);
      
      // Refresh data
      fetchEmails();
      fetchStatistics();
      setSelectedEmails([]);
      setShowBulkActions(false);
      
    } catch (err) {
      setError(err.message);
    }
  };

  const toggleEmailSelection = (quarantineId) => {
    setSelectedEmails(prev => 
      prev.includes(quarantineId) 
        ? prev.filter(id => id !== quarantineId)
        : [...prev, quarantineId]
    );
  };

  const selectAllEmails = () => {
    setSelectedEmails(emails.map(email => email.id));
  };

  const clearSelection = () => {
    setSelectedEmails([]);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'quarantined':
        return 'text-orange-600 bg-orange-100';
      case 'released':
        return 'text-green-600 bg-green-100';
      case 'deleted':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getReasonColor = (reason) => {
    switch (reason) {
      case 'suspicious':
        return 'text-yellow-600 bg-yellow-100';
      case 'malicious':
        return 'text-red-600 bg-red-100';
      case 'policy_violation':
        return 'text-purple-600 bg-purple-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getThreatScoreColor = (score) => {
    if (score >= 0.8) return 'text-red-600';
    if (score >= 0.6) return 'text-orange-600';
    if (score >= 0.4) return 'text-yellow-600';
    return 'text-green-600';
  };

  if (loading && emails.length === 0) {
    return <div className="p-4">Loading quarantined emails...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Email Quarantine Management</h3>
        <div className="flex gap-2">
          {selectedEmails.length > 0 && (
            <button
              onClick={() => setShowBulkActions(!showBulkActions)}
              className="px-4 py-2 bg-privik-blue-600 text-white rounded hover:bg-privik-blue-700"
            >
              Bulk Actions ({selectedEmails.length})
            </button>
          )}
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
          <h4 className="font-medium text-gray-900 mb-3">Quarantine Statistics</h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-gray-900">{statistics.total_quarantined}</div>
              <div className="text-sm text-gray-600">Total Quarantined</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">{statistics.active_quarantined}</div>
              <div className="text-sm text-gray-600">Currently Quarantined</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">{statistics.status_statistics?.released || 0}</div>
              <div className="text-sm text-gray-600">Released</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-red-600">{statistics.status_statistics?.deleted || 0}</div>
              <div className="text-sm text-gray-600">Deleted</div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="mb-4 flex gap-4">
        <select
          value={filters.status}
          onChange={(e) => setFilters({...filters, status: e.target.value})}
          className="px-3 py-2 border border-gray-300 rounded-md"
        >
          <option value="">All Statuses</option>
          <option value="quarantined">Quarantined</option>
          <option value="released">Released</option>
          <option value="deleted">Deleted</option>
        </select>
        
        <select
          value={filters.reason}
          onChange={(e) => setFilters({...filters, reason: e.target.value})}
          className="px-3 py-2 border border-gray-300 rounded-md"
        >
          <option value="">All Reasons</option>
          <option value="suspicious">Suspicious</option>
          <option value="malicious">Malicious</option>
          <option value="policy_violation">Policy Violation</option>
        </select>
      </div>

      {/* Bulk Actions */}
      {showBulkActions && (
        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h5 className="font-medium text-blue-900 mb-2">Bulk Actions</h5>
          <div className="flex gap-2">
            <button
              onClick={() => handleBulkAction('release')}
              className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
            >
              Release All
            </button>
            <button
              onClick={() => handleBulkAction('delete')}
              className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
            >
              Delete All
            </button>
            <button
              onClick={() => handleBulkAction('whitelist')}
              className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
            >
              Whitelist Senders
            </button>
            <button
              onClick={() => handleBulkAction('blacklist')}
              className="px-3 py-1 bg-purple-600 text-white rounded text-sm hover:bg-purple-700"
            >
              Blacklist Senders
            </button>
            <button
              onClick={() => setShowBulkActions(false)}
              className="px-3 py-1 bg-gray-600 text-white rounded text-sm hover:bg-gray-700"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Emails Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                <input
                  type="checkbox"
                  checked={selectedEmails.length === emails.length && emails.length > 0}
                  onChange={selectedEmails.length === emails.length ? clearSelection : selectAllEmails}
                  className="rounded border-gray-300 text-privik-blue-600 focus:ring-privik-blue-500"
                />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Email
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Reason
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Threat Score
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Quarantined
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {emails.map((email) => (
              <tr key={email.id}>
                <td className="px-6 py-4 whitespace-nowrap">
                  <input
                    type="checkbox"
                    checked={selectedEmails.includes(email.id)}
                    onChange={() => toggleEmailSelection(email.id)}
                    className="rounded border-gray-300 text-privik-blue-600 focus:ring-privik-blue-500"
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div>
                    <div className="text-sm font-medium text-gray-900">
                      Email ID: {email.email_id}
                    </div>
                    <div className="text-sm text-gray-500">
                      {email.analysis_details?.email?.subject || 'No subject'}
                    </div>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getReasonColor(email.quarantine_reason)}`}>
                    {email.quarantine_reason}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className={`text-sm font-medium ${getThreatScoreColor(email.threat_score)}`}>
                    {Math.round(email.threat_score * 100)}%
                  </div>
                  <div className="text-xs text-gray-500">
                    {Math.round(email.confidence * 100)}% confidence
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getStatusColor(email.status)}`}>
                    {email.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(email.quarantined_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex gap-1">
                    <button
                      onClick={() => fetchEmailDetail(email.id)}
                      className="text-privik-blue-600 hover:text-privik-blue-900"
                    >
                      View
                    </button>
                    {email.status === 'quarantined' && (
                      <>
                        <button
                          onClick={() => handleQuarantineAction(email.id, 'release')}
                          className="text-green-600 hover:text-green-900"
                        >
                          Release
                        </button>
                        <button
                          onClick={() => handleQuarantineAction(email.id, 'delete')}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination.total > pagination.limit && (
        <div className="mt-4 flex justify-between items-center">
          <div className="text-sm text-gray-700">
            Showing {pagination.offset + 1} to {Math.min(pagination.offset + pagination.limit, pagination.total)} of {pagination.total} emails
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

      {emails.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No quarantined emails found.
        </div>
      )}

      {/* Email Detail Modal */}
      {showEmailDetail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-96 overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h4 className="text-lg font-semibold">Email Details</h4>
              <button
                onClick={() => setShowEmailDetail(null)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            {showEmailDetail.email && (
              <div className="space-y-4">
                <div>
                  <h5 className="font-medium">Subject</h5>
                  <p className="text-gray-600">{showEmailDetail.email.subject}</p>
                </div>
                <div>
                  <h5 className="font-medium">Sender</h5>
                  <p className="text-gray-600">{showEmailDetail.email.sender}</p>
                </div>
                <div>
                  <h5 className="font-medium">Content Preview</h5>
                  <p className="text-gray-600 text-sm">{showEmailDetail.email.content_preview}</p>
                </div>
              </div>
            )}
            
            <div className="mt-6 flex gap-2">
              {showEmailDetail.quarantine.status === 'quarantined' && (
                <>
                  <button
                    onClick={() => {
                      handleQuarantineAction(showEmailDetail.quarantine.id, 'release');
                    }}
                    className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    Release
                  </button>
                  <button
                    onClick={() => {
                      handleQuarantineAction(showEmailDetail.quarantine.id, 'delete');
                    }}
                    className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
                  >
                    Delete
                  </button>
                  <button
                    onClick={() => {
                      handleQuarantineAction(showEmailDetail.quarantine.id, 'whitelist');
                    }}
                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    Whitelist Sender
                  </button>
                  <button
                    onClick={() => {
                      handleQuarantineAction(showEmailDetail.quarantine.id, 'blacklist');
                    }}
                    className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
                  >
                    Blacklist Sender
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default QuarantineManager;
