import React from 'react';
import { useQuery } from 'react-query';
import {
  EnvelopeIcon,
  ExclamationTriangleIcon,
  UsersIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline';
import StatCard from '../components/StatCard';
import AlertCard from '../components/AlertCard';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

// Mock data - replace with actual API calls
const mockDashboardData = {
  summary: {
    totalEmails: 1247,
    threatsDetected: 23,
    activeUsers: 156,
    protectionRate: 98.2,
  },
  hourlyStats: [
    { hour: '00:00', emails: 45, threats: 2 },
    { hour: '04:00', emails: 32, threats: 1 },
    { hour: '08:00', emails: 89, threats: 4 },
    { hour: '12:00', emails: 156, threats: 7 },
    { hour: '16:00', emails: 134, threats: 5 },
    { hour: '20:00', emails: 78, threats: 3 },
  ],
  recentAlerts: [
    {
      id: 1,
      title: 'Suspicious Link Detected',
      description: 'User clicked on potentially malicious link from unknown sender',
      severity: 'high',
      timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    },
    {
      id: 2,
      title: 'File Attachment Analysis Complete',
      description: 'PDF file flagged for suspicious behavior patterns',
      severity: 'medium',
      timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    },
    {
      id: 3,
      title: 'User Risk Score Increased',
      description: 'User john.doe@company.com risk score increased by 15%',
      severity: 'low',
      timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    },
  ],
};

function Dashboard() {
  // In a real app, you would use actual API calls here
  const { data: dashboardData, isLoading, error } = useQuery(
    'dashboard',
    () => Promise.resolve(mockDashboardData),
    { refetchInterval: 30000 } // Refresh every 30 seconds
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-privik-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">Error loading dashboard data</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Security Operations Dashboard</h1>
        <p className="text-gray-600">Real-time overview of email security threats and user activity</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Emails"
          value={dashboardData.summary.totalEmails.toLocaleString()}
          change="+12%"
          changeType="positive"
          icon={EnvelopeIcon}
        />
        <StatCard
          title="Threats Detected"
          value={dashboardData.summary.threatsDetected}
          change="+3"
          changeType="negative"
          icon={ExclamationTriangleIcon}
        />
        <StatCard
          title="Active Users"
          value={dashboardData.summary.activeUsers}
          change="+5"
          changeType="positive"
          icon={UsersIcon}
        />
        <StatCard
          title="Protection Rate"
          value={`${dashboardData.summary.protectionRate}%`}
          change="+0.5%"
          changeType="positive"
          icon={ShieldCheckIcon}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Email Activity Chart */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Email Activity (24h)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dashboardData.hourlyStats}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="emails" stroke="#3b82f6" strokeWidth={2} />
              <Line type="monotone" dataKey="threats" stroke="#ef4444" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Threat Distribution */}
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Threat Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dashboardData.hourlyStats}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hour" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="threats" fill="#ef4444" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Alerts */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Recent Alerts</h3>
          <button className="text-sm text-privik-blue-600 hover:text-privik-blue-700">
            View All
          </button>
        </div>
        <div className="space-y-4">
          {dashboardData.recentAlerts.map((alert) => (
            <AlertCard key={alert.id} alert={alert} />
          ))}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
