import React from 'react';

function Incidents() {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-900">Security Incidents</h1>
        <p className="text-gray-600 mt-2">Manage and track security incidents</p>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Incidents</h2>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg">
            <div>
              <h3 className="font-medium text-red-900">Phishing Campaign Detected</h3>
              <p className="text-sm text-red-700">Multiple phishing emails targeting employees</p>
            </div>
            <span className="px-2 py-1 text-xs font-medium bg-red-100 text-red-800 rounded-full">
              High Priority
            </span>
          </div>
          <div className="flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div>
              <h3 className="font-medium text-yellow-900">Suspicious File Attachment</h3>
              <p className="text-sm text-yellow-700">Unknown file type detected in email</p>
            </div>
            <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
              Medium Priority
            </span>
          </div>
          <div className="flex items-center justify-between p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div>
              <h3 className="font-medium text-blue-900">Unusual Login Pattern</h3>
              <p className="text-sm text-blue-700">Multiple failed login attempts detected</p>
            </div>
            <span className="px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
              Low Priority
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Incidents;