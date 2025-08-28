import React from 'react';
import { useQuery } from 'react-query';
import { UsersIcon, ExclamationTriangleIcon, ArrowTrendingUpIcon } from '@heroicons/react/24/outline';

// Mock data
const mockUserData = {
  users: [
    {
      id: 1,
      email: 'john.doe@company.com',
      name: 'John Doe',
      riskScore: 75,
      lastActivity: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
      suspiciousActions: 3,
      department: 'Finance',
    },
    {
      id: 2,
      email: 'jane.smith@company.com',
      name: 'Jane Smith',
      riskScore: 25,
      lastActivity: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
      suspiciousActions: 0,
      department: 'HR',
    },
    {
      id: 3,
      email: 'bob.wilson@company.com',
      name: 'Bob Wilson',
      riskScore: 90,
      lastActivity: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
      suspiciousActions: 5,
      department: 'IT',
    },
  ],
  stats: {
    totalUsers: 156,
    highRiskUsers: 12,
    averageRiskScore: 45,
  },
};

function UserRisk() {
  const { data: userData, isLoading } = useQuery(
    'userRisk',
    () => Promise.resolve(mockUserData),
    { refetchInterval: 60000 }
  );

  const getRiskScoreColor = (score) => {
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
      <div>
        <h1 className="text-2xl font-bold text-gray-900">User Risk Management</h1>
        <p className="text-gray-600">Monitor user behavior and risk profiles</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center">
            <UsersIcon className="h-8 w-8 text-privik-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Users</p>
              <p className="text-2xl font-bold text-gray-900">{userData.stats.totalUsers}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-8 w-8 text-privik-red-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">High Risk Users</p>
              <p className="text-2xl font-bold text-gray-900">{userData.stats.highRiskUsers}</p>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <ArrowTrendingUpIcon className="h-8 w-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Avg Risk Score</p>
              <p className="text-2xl font-bold text-gray-900">{userData.stats.averageRiskScore}</p>
            </div>
          </div>
        </div>
      </div>

      {/* User List */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">User Risk Profiles</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Department</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Risk Score</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Suspicious Actions</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Last Activity</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {userData.users.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{user.name}</div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {user.department}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRiskScoreColor(user.riskScore)}`}>
                      {user.riskScore}/100
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {user.suspiciousActions}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(user.lastActivity).toLocaleString()}
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

export default UserRisk;
