import React, { useState } from 'react';
import { useQuery } from 'react-query';
import {
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

// Mock data - replace with actual API calls
const mockEmails = [
  {
    id: 1,
    subject: 'Urgent: Invoice Payment Required',
    sender: 'billing@company-invoice.com',
    recipient: 'john.doe@company.com',
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    threatScore: 85,
    status: 'analyzing',
    hasAttachments: true,
    analysis: {
      isPhishing: true,
      isBEC: true,
      suspiciousKeywords: ['urgent', 'payment', 'invoice'],
      senderReputation: 'low',
    },
  },
  {
    id: 2,
    subject: 'Meeting Schedule for Q4',
    sender: 'hr@company.com',
    recipient: 'jane.smith@company.com',
    timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    threatScore: 15,
    status: 'safe',
    hasAttachments: false,
    analysis: {
      isPhishing: false,
      isBEC: false,
      suspiciousKeywords: [],
      senderReputation: 'high',
    },
  },
  {
    id: 3,
    subject: 'Your Account Has Been Suspended',
    sender: 'security@bank-verify.com',
    recipient: 'user@company.com',
    timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
    threatScore: 92,
    status: 'blocked',
    hasAttachments: false,
    analysis: {
      isPhishing: true,
      isBEC: false,
      suspiciousKeywords: ['suspended', 'account', 'verify'],
      senderReputation: 'low',
    },
  },
];

function EmailAnalysis() {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const { data: emails, isLoading } = useQuery(
    'emails',
    () => Promise.resolve(mockEmails),
    { refetchInterval: 30000 }
  );

  const filteredEmails = emails?.filter(email => {
    const matchesSearch = email.subject.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         email.sender.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = statusFilter === 'all' || email.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const getStatusIcon = (status) => {
    switch (status) {
      case 'safe':
        return <CheckCircleIcon className="h-5 w-5 text-privik-green-600" />;
      case 'analyzing':
        return <ClockIcon className="h-5 w-5 text-yellow-600" />;
      case 'blocked':
        return <ExclamationTriangleIcon className="h-5 w-5 text-privik-red-600" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-600" />;
    }
  };

  const getThreatScoreColor = (score) => {
    if (score >= 80) return 'text-privik-red-600 bg-privik-red-100';
    if (score >= 50) return 'text-yellow-600 bg-yellow-100';
    return 'text-privik-green-600 bg-privik-green-100';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-privik-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Email Analysis</h1>
        <p className="text-gray-600">Monitor and analyze email threats in real-time</p>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search emails..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="input-field pl-10"
          />
        </div>
        <div className="flex items-center space-x-2">
          <FunnelIcon className="h-5 w-5 text-gray-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input-field"
          >
            <option value="all">All Status</option>
            <option value="safe">Safe</option>
            <option value="analyzing">Analyzing</option>
            <option value="blocked">Blocked</option>
          </select>
        </div>
      </div>

      {/* Email List */}
      <div className="card">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Email
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Threat Score
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Time
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredEmails?.map((email) => (
                <tr key={email.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">
                        {email.subject}
                      </div>
                      <div className="text-sm text-gray-500">
                        {email.sender} → {email.recipient}
                      </div>
                      {email.hasAttachments && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                          Attachment
                        </span>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getThreatScoreColor(email.threatScore)}`}>
                      {email.threatScore}/100
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      {getStatusIcon(email.status)}
                      <span className="ml-2 text-sm text-gray-900 capitalize">
                        {email.status}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(email.timestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button className="text-privik-blue-600 hover:text-privik-blue-900">
                      <EyeIcon className="h-5 w-5" />
                    </button>
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

export default EmailAnalysis;
