import React from 'react';

function ThreatIntel() {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-900">Threat Intelligence</h1>
        <p className="text-gray-600 mt-2">Monitor and analyze security threats</p>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Threat Intelligence Dashboard</h2>
        <div className="space-y-4">
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <h3 className="font-medium text-red-900">High Priority Threats</h3>
            <p className="text-sm text-red-700 mt-1">3 active high-priority threats detected</p>
          </div>
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h3 className="font-medium text-yellow-900">Medium Priority Threats</h3>
            <p className="text-sm text-yellow-700 mt-1">7 medium-priority threats detected</p>
          </div>
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="font-medium text-green-900">Low Priority Threats</h3>
            <p className="text-sm text-green-700 mt-1">12 low-priority threats detected</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ThreatIntel;