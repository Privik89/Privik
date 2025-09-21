import React, { useState, useRef } from 'react';

const BulkDomainManager = () => {
  const [activeTab, setActiveTab] = useState('import');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [importForm, setImportForm] = useState({
    list_type: 'blacklist',
    created_by: '',
    validate_domains: true,
    score_domains: true
  });
  const [exportForm, setExportForm] = useState({
    list_type: 'all',
    active_only: true,
    include_metadata: true
  });
  const fileInputRef = useRef(null);

  const handleImport = async (e) => {
    e.preventDefault();
    if (!fileInputRef.current?.files[0]) {
      setError('Please select a file to import');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('file', fileInputRef.current.files[0]);
      formData.append('list_type', importForm.list_type);
      formData.append('created_by', importForm.created_by || 'bulk_import');
      formData.append('validate_domains', importForm.validate_domains);
      formData.append('score_domains', importForm.score_domains);

      const response = await fetch('/api/ui/bulk-domains/domains/bulk/import/csv', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Import failed');
      }

      const data = await response.json();
      setResult(data);
      
      // Clear file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format) => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (exportForm.list_type !== 'all') {
        params.append('list_type', exportForm.list_type);
      }
      params.append('active_only', exportForm.active_only);
      
      if (format === 'json') {
        params.append('include_metadata', exportForm.include_metadata);
      }

      const response = await fetch(`/api/ui/bulk-domains/domains/bulk/export/${format}?${params}`);
      
      if (!response.ok) {
        throw new Error('Export failed');
      }

      // Download file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `domains_export.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setResult({
        message: `Export completed successfully`,
        format: format,
        exported_at: new Date().toISOString()
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // const getResultColor = (type) => {
  //   switch (type) {
  //     case 'success':
  //       return 'text-green-600 bg-green-100';
  //     case 'warning':
  //       return 'text-yellow-600 bg-yellow-100';
  //     case 'error':
  //       return 'text-red-600 bg-red-100';
  //     default:
  //       return 'text-blue-600 bg-blue-100';
  //   }
  // };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">Bulk Domain Management</h3>
        <div className="flex space-x-1 bg-gray-100 rounded-lg p-1">
          <button
            onClick={() => setActiveTab('import')}
            className={`px-3 py-1 rounded text-sm font-medium ${
              activeTab === 'import' 
                ? 'bg-white text-privik-blue-600 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Import
          </button>
          <button
            onClick={() => setActiveTab('export')}
            className={`px-3 py-1 rounded text-sm font-medium ${
              activeTab === 'export' 
                ? 'bg-white text-privik-blue-600 shadow-sm' 
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Export
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {result && (
        <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">
            {result.message || 'Operation completed'}
          </h4>
          {result.successful_imports !== undefined && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="font-medium text-blue-900">{result.successful_imports}</div>
                <div className="text-blue-700">Imported</div>
              </div>
              <div>
                <div className="font-medium text-blue-900">{result.validation_errors}</div>
                <div className="text-blue-700">Validation Errors</div>
              </div>
              <div>
                <div className="font-medium text-blue-900">{result.duplicate_domains}</div>
                <div className="text-blue-700">Duplicates</div>
              </div>
              <div>
                <div className="font-medium text-blue-900">{result.total_processed}</div>
                <div className="text-blue-700">Total Processed</div>
              </div>
            </div>
          )}
          {result.errors && result.errors.length > 0 && (
            <div className="mt-3">
              <h5 className="font-medium text-red-900 mb-2">Errors:</h5>
              <div className="max-h-32 overflow-y-auto">
                {result.errors.slice(0, 10).map((error, index) => (
                  <div key={index} className="text-sm text-red-700">{error}</div>
                ))}
                {result.errors.length > 10 && (
                  <div className="text-sm text-red-600">... and {result.errors.length - 10} more errors</div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'import' && (
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-4">Import Domains</h4>
          
          <form onSubmit={handleImport} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                CSV File
              </label>
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv"
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded file:border-0 file:text-sm file:font-medium file:bg-privik-blue-50 file:text-privik-blue-700 hover:file:bg-privik-blue-100"
              />
              <p className="text-xs text-gray-500 mt-1">
                CSV should contain columns: domain, reason (optional)
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  List Type
                </label>
                <select
                  value={importForm.list_type}
                  onChange={(e) => setImportForm({...importForm, list_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-privik-blue-500"
                >
                  <option value="blacklist">Blacklist</option>
                  <option value="whitelist">Whitelist</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Created By
                </label>
                <input
                  type="text"
                  value={importForm.created_by}
                  onChange={(e) => setImportForm({...importForm, created_by: e.target.value})}
                  placeholder="bulk_import"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-privik-blue-500"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={importForm.validate_domains}
                  onChange={(e) => setImportForm({...importForm, validate_domains: e.target.checked})}
                  className="rounded border-gray-300 text-privik-blue-600 focus:ring-privik-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">Validate domain format</span>
              </label>
              
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={importForm.score_domains}
                  onChange={(e) => setImportForm({...importForm, score_domains: e.target.checked})}
                  className="rounded border-gray-300 text-privik-blue-600 focus:ring-privik-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">Score domains with reputation service</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full px-4 py-2 bg-privik-blue-600 text-white rounded hover:bg-privik-blue-700 disabled:opacity-50"
            >
              {loading ? 'Importing...' : 'Import Domains'}
            </button>
          </form>
        </div>
      )}

      {activeTab === 'export' && (
        <div>
          <h4 className="text-md font-medium text-gray-900 mb-4">Export Domains</h4>
          
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  List Type
                </label>
                <select
                  value={exportForm.list_type}
                  onChange={(e) => setExportForm({...exportForm, list_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-privik-blue-500"
                >
                  <option value="all">All Domains</option>
                  <option value="blacklist">Blacklist Only</option>
                  <option value="whitelist">Whitelist Only</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Status
                </label>
                <select
                  value={exportForm.active_only}
                  onChange={(e) => setExportForm({...exportForm, active_only: e.target.value === 'true'})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-privik-blue-500"
                >
                  <option value={true}>Active Only</option>
                  <option value={false}>All (including inactive)</option>
                </select>
              </div>
            </div>

            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={exportForm.include_metadata}
                  onChange={(e) => setExportForm({...exportForm, include_metadata: e.target.checked})}
                  className="rounded border-gray-300 text-privik-blue-600 focus:ring-privik-blue-500"
                />
                <span className="ml-2 text-sm text-gray-700">Include export metadata (JSON only)</span>
              </label>
            </div>

            <div className="flex space-x-4">
              <button
                onClick={() => handleExport('csv')}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
              >
                {loading ? 'Exporting...' : 'Export CSV'}
              </button>
              
              <button
                onClick={() => handleExport('json')}
                disabled={loading}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
              >
                {loading ? 'Exporting...' : 'Export JSON'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BulkDomainManager;
