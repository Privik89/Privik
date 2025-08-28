import React from 'react';
import { useQuery } from 'react-query';
import { ExclamationTriangleIcon, GlobeAltIcon, LinkIcon } from '@heroicons/react/24/outline';

// Mock data
const mockThreatData = {
  indicators: [
    {
      id: 1,
      type: 'domain',
      value: 'malicious-site.com',
      threatType: 'phishing',
      confidence: 95,
      firstSeen: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(),
      lastSeen: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    },
    {
      id: 2,
      type: 'ip',
      value: '192.168.1.100',
      threatType: 'malware',
      confidence: 87,
      firstSeen: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
      lastSeen: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    },
  ],
  stats: {
    totalIndicators: 156,
    activeThreats: 23,
    blockedAttacks: 89,
  },
};

function ThreatIntel() {
  const { data: threatData, isLoading } = useQuery(
    'threatIntel',
    () => Promise.resolve(mockThreatData),
    { refetchInterval: 60000 }
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-privik-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Threat Intelligence</h1>
        <p className="text-gray-600">Monitor threat indicators and intelligence feeds</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-8 w-8 text-privik-red-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Indicators</p>
              <p className="text-2xl font-bold text-gray-900">{threatData.stats.totalIndicators}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <GlobeAltIcon className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Active Threats</p>
              <p className="text-2xl font-bold text-gray-900">{threatData.stats.activeThreats}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <LinkIcon className="h-8 w-8 text-privik-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Blocked Attacks</p>
              <p className="text-2xl font-bold text-gray-900">{threatData.stats.blockedAttacks}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Threat Indicators */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Threat Indicators</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Threat Type</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Confidence</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Seen</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {threatData.indicators.map((indicator) => (
                <tr key={indicator.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {indicator.type.toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {indicator.value}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-privik-red-100 text-privik-red-800">
                      {indicator.threatType}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {indicator.confidence}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(indicator.lastSeen).toLocaleString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default ThreatIntel;
