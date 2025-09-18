import React, { useState, useEffect } from 'react';

const DomainListsCard = () => {
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [newDomain, setNewDomain] = useState('');
  const [newListType, setNewListType] = useState('blacklist');
  const [newReason, setNewReason] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    fetchDomains();
  }, [filterType]);

  const fetchDomains = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (filterType !== 'all') {
        params.append('list_type', filterType);
      }
      
      const response = await fetch(`/api/ui/domain-lists/domains?${params}`);
      if (!response.ok) throw new Error('Failed to fetch domains');
      
      const data = await response.json();
      setDomains(data.domains || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const addDomain = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/ui/domain-lists/domains', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          domain: newDomain,
          list_type: newListType,
          reason: newReason
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to add domain');
      }
      
      setNewDomain('');
      setNewReason('');
      setShowAddForm(false);
      fetchDomains();
    } catch (err) {
      setError(err.message);
    }
  };

  const removeDomain = async (id) => {
    if (!confirm('Are you sure you want to remove this domain?')) return;
    
    try {
      const response = await fetch(`/api/ui/domain-lists/domains/${id}`, {
        method: 'DELETE'
      });
      
      if (!response.ok) throw new Error('Failed to remove domain');
      
      fetchDomains();
    } catch (err) {
      setError(err.message);
    }
  };

  const getListTypeColor = (type) => {
    return type === 'whitelist' ? 'text-green-600 bg-green-100' : 'text-red-600 bg-red-100';
  };

  if (loading) return <div className="p-4">Loading domains...</div>;

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Domain Lists</h3>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="px-4 py-2 bg-privik-blue-600 text-white rounded hover:bg-privik-blue-700"
        >
          Add Domain
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      <div className="mb-4">
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md"
        >
          <option value="all">All Domains</option>
          <option value="whitelist">Whitelist Only</option>
          <option value="blacklist">Blacklist Only</option>
        </select>
      </div>

      {showAddForm && (
        <form onSubmit={addDomain} className="mb-6 p-4 border border-gray-200 rounded-lg">
          <h4 className="text-md font-medium mb-3">Add New Domain</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Domain</label>
              <input
                type="text"
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
                placeholder="example.com"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">List Type</label>
              <select
                value={newListType}
                onChange={(e) => setNewListType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="blacklist">Blacklist</option>
                <option value="whitelist">Whitelist</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Reason</label>
              <input
                type="text"
                value={newReason}
                onChange={(e) => setNewReason(e.target.value)}
                placeholder="Optional reason"
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>
          <div className="mt-3 flex gap-2">
            <button
              type="submit"
              className="px-4 py-2 bg-privik-blue-600 text-white rounded hover:bg-privik-blue-700"
            >
              Add Domain
            </button>
            <button
              type="button"
              onClick={() => setShowAddForm(false)}
              className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Domain
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Type
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Reason
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Created
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {domains.map((domain) => (
              <tr key={domain.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {domain.domain}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getListTypeColor(domain.list_type)}`}>
                    {domain.list_type}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm text-gray-500">
                  {domain.reason || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(domain.created_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <button
                    onClick={() => removeDomain(domain.id)}
                    className="text-red-600 hover:text-red-900"
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {domains.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No domains found. Add your first domain to get started.
        </div>
      )}
    </div>
  );
};

export default DomainListsCard;
