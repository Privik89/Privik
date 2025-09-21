import React from 'react';
import { ShieldCheckIcon, ExclamationTriangleIcon, ChartBarIcon, UsersIcon } from '@heroicons/react/24/outline';

function Dashboard() {
  const stats = [
    { name: 'Emails Scanned', value: '1,234', change: '+12%', changeType: 'positive' },
    { name: 'Threats Detected', value: '23', change: '+5%', changeType: 'positive' },
    { name: 'Quarantined', value: '8', change: '-2%', changeType: 'negative' },
    { name: 'Active Users', value: '156', change: '+3%', changeType: 'positive' },
  ];

  const recentActivity = [
    { id: 1, type: 'threat', message: 'Phishing attempt blocked', time: '2 minutes ago' },
    { id: 2, type: 'quarantine', message: 'Suspicious email quarantined', time: '5 minutes ago' },
    { id: 3, type: 'scan', message: 'Bulk email scan completed', time: '10 minutes ago' },
    { id: 4, type: 'user', message: 'New user login detected', time: '15 minutes ago' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-900">Email Security Dashboard</h1>
        <p className="text-gray-600 mt-2">Monitor and manage your email security in real-time</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className="bg-white rounded-lg shadow-sm p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.name}</p>
                <p className="text-2xl font-bold text-gray-900">{stat.value}</p>
              </div>
              <div className={`text-sm font-medium ${
                stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
              }`}>
                {stat.change}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div className="space-y-3">
          {recentActivity.map((activity) => (
            <div key={activity.id} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
              <div className="flex-shrink-0">
                {activity.type === 'threat' && (
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />
                )}
                {activity.type === 'quarantine' && (
                  <ShieldCheckIcon className="h-5 w-5 text-yellow-500" />
                )}
                {activity.type === 'scan' && (
                  <ChartBarIcon className="h-5 w-5 text-blue-500" />
                )}
                {activity.type === 'user' && (
                  <UsersIcon className="h-5 w-5 text-green-500" />
                )}
              </div>
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-900">{activity.message}</p>
                <p className="text-xs text-gray-500">{activity.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button className="bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200">
            Scan New Emails
          </button>
          <button className="bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200">
            View Quarantine
          </button>
          <button className="bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-lg transition-colors duration-200">
            Generate Report
          </button>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;