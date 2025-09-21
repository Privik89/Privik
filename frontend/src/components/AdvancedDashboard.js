import React, { useState, useEffect } from 'react';
import { useDashboardData } from '../hooks/useApi';

function AdvancedDashboard() {
  const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  // Use the API hook for dashboard data
  const { data: dashboardData, loading, error, refresh } = useDashboardData(selectedTimeRange);

  // Auto-refresh functionality
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(() => {
      console.log('Auto-refreshing dashboard data...');
      refresh();
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, [autoRefresh, refresh]);

  const timeRanges = [
    { value: '1h', label: 'Last Hour' },
    { value: '24h', label: 'Last 24 Hours' },
    { value: '7d', label: 'Last 7 Days' },
    { value: '30d', label: 'Last 30 Days' }
  ];

  // Get data from API or use fallback
  const stats = dashboardData?.stats || {
    emailsScanned: 12456,
    threatsDetected: 23,
    quarantined: 8,
    detectionRate: 99.2
  };

  const threatTypes = dashboardData?.metrics?.threatTypes || [
    { name: 'Phishing', count: 12, percentage: 52, color: '#dc2626' },
    { name: 'Malware', count: 7, percentage: 30, color: '#f59e0b' },
    { name: 'Spam', count: 4, percentage: 18, color: '#10b981' }
  ];

  const recentThreats = dashboardData?.activity || [
    {
      id: 1,
      type: 'Phishing',
      severity: 'High',
      sender: 'suspicious@fake-bank.com',
      subject: 'Urgent: Verify Your Account',
      time: '2 minutes ago',
      status: 'Blocked'
    },
    {
      id: 2,
      type: 'Malware',
      severity: 'Critical',
      sender: 'noreply@invoice-system.com',
      subject: 'Invoice #INV-2024-001',
      time: '5 minutes ago',
      status: 'Quarantined'
    },
    {
      id: 3,
      type: 'Spam',
      severity: 'Low',
      sender: 'promotions@retail-store.com',
      subject: 'Special Offer - 50% Off Everything!',
      time: '8 minutes ago',
      status: 'Filtered'
    }
  ];

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'Critical': return '#dc2626';
      case 'High': return '#f59e0b';
      case 'Medium': return '#eab308';
      case 'Low': return '#10b981';
      default: return '#6b7280';
    }
  };

  if (loading) {
    return (
      <div style={{ 
        minHeight: '100vh', 
        backgroundColor: '#f9fafb', 
        padding: '20px',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <div style={{
          textAlign: 'center',
          backgroundColor: 'white',
          borderRadius: '8px',
          padding: '40px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
        }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: '4px solid #e5e7eb',
            borderTop: '4px solid #2563eb',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 16px'
          }}></div>
          <p style={{ color: '#6b7280', fontSize: '16px' }}>Loading Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#f9fafb', 
      padding: '20px',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto'
      }}>
        {/* Connection Status */}
        {error && (
          <div style={{
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            padding: '12px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}>
            <span style={{ fontSize: '16px' }}>⚠️</span>
            <div>
              <p style={{ fontSize: '14px', fontWeight: '500', color: '#dc2626', margin: '0 0 4px 0' }}>
                Connection Error
              </p>
              <p style={{ fontSize: '12px', color: '#991b1b', margin: 0 }}>
                {error} - Using cached data. Check backend connection.
              </p>
            </div>
            <button
              onClick={refresh}
              style={{
                marginLeft: 'auto',
                padding: '4px 8px',
                backgroundColor: '#dc2626',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                fontSize: '12px',
                cursor: 'pointer'
              }}
            >
              Retry
            </button>
          </div>
        )}

        {/* Header */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '24px'
        }}>
          <div>
            <h1 style={{ 
              fontSize: '28px', 
              fontWeight: 'bold', 
              color: '#111827',
              marginBottom: '4px'
            }}>
              🛡️ Email Security Dashboard
            </h1>
            <p style={{ 
              color: '#6b7280', 
              fontSize: '14px'
            }}>
              Real-time monitoring and threat analysis
            </p>
          </div>
          
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <select
              value={selectedTimeRange}
              onChange={(e) => setSelectedTimeRange(e.target.value)}
              style={{
                padding: '8px 12px',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                fontSize: '14px',
                backgroundColor: 'white'
              }}
            >
              {timeRanges.map(range => (
                <option key={range.value} value={range.value}>
                  {range.label}
                </option>
              ))}
            </select>
            
            <button
              onClick={() => setAutoRefresh(!autoRefresh)}
              style={{
                padding: '8px 16px',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer',
                backgroundColor: autoRefresh ? '#16a34a' : '#6b7280',
                color: 'white'
              }}
            >
              {autoRefresh ? '🔄 Auto Refresh ON' : '⏸️ Auto Refresh OFF'}
            </button>
          </div>
        </div>

        {/* Key Metrics */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '20px',
          marginBottom: '32px'
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#374151', margin: 0 }}>
                Emails Scanned
              </h3>
              <span style={{ fontSize: '24px' }}>📧</span>
            </div>
            <p style={{ fontSize: '32px', fontWeight: 'bold', color: '#111827', margin: '0 0 8px 0' }}>
              {stats.emailsScanned?.toLocaleString() || '12,456'}
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '14px', color: '#16a34a', fontWeight: '500' }}>
                ↗ +12.5%
              </span>
              <span style={{ fontSize: '12px', color: '#6b7280' }}>
                vs last 24h
              </span>
            </div>
          </div>

          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#374151', margin: 0 }}>
                Threats Detected
              </h3>
              <span style={{ fontSize: '24px' }}>⚠️</span>
            </div>
            <p style={{ fontSize: '32px', fontWeight: 'bold', color: '#dc2626', margin: '0 0 8px 0' }}>
              {stats.threatsDetected || '23'}
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '14px', color: '#dc2626', fontWeight: '500' }}>
                ↗ +5.2%
              </span>
              <span style={{ fontSize: '12px', color: '#6b7280' }}>
                vs last 24h
              </span>
            </div>
          </div>

          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#374151', margin: 0 }}>
                Quarantined
              </h3>
              <span style={{ fontSize: '24px' }}>🔒</span>
            </div>
            <p style={{ fontSize: '32px', fontWeight: 'bold', color: '#f59e0b', margin: '0 0 8px 0' }}>
              {stats.quarantined || '8'}
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '14px', color: '#16a34a', fontWeight: '500' }}>
                ↘ -2.1%
              </span>
              <span style={{ fontSize: '12px', color: '#6b7280' }}>
                vs last 24h
              </span>
            </div>
          </div>

          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#374151', margin: 0 }}>
                Detection Rate
              </h3>
              <span style={{ fontSize: '24px' }}>🎯</span>
            </div>
            <p style={{ fontSize: '32px', fontWeight: 'bold', color: '#16a34a', margin: '0 0 8px 0' }}>
              {stats.detectionRate || '99.2'}%
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '14px', color: '#16a34a', fontWeight: '500' }}>
                ↗ +0.3%
              </span>
              <span style={{ fontSize: '12px', color: '#6b7280' }}>
                vs last 24h
              </span>
            </div>
          </div>
        </div>

        {/* Charts and Analytics */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '24px',
          marginBottom: '32px'
        }}>
          {/* Threat Types Chart */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            border: '1px solid #e5e7eb'
          }}>
            <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '20px' }}>
              Threat Types Distribution
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {threatTypes.map((threat, index) => (
                <div key={index}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <span style={{ fontSize: '14px', fontWeight: '500', color: '#374151' }}>
                      {threat.name}
                    </span>
                    <span style={{ fontSize: '14px', fontWeight: '600', color: '#111827' }}>
                      {threat.count} ({threat.percentage}%)
                    </span>
                  </div>
                  <div style={{
                    width: '100%',
                    height: '8px',
                    backgroundColor: '#f3f4f6',
                    borderRadius: '4px',
                    overflow: 'hidden'
                  }}>
                    <div style={{
                      width: `${threat.percentage}%`,
                      height: '100%',
                      backgroundColor: threat.color,
                      borderRadius: '4px',
                      transition: 'width 0.3s ease'
                    }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Threats */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            border: '1px solid #e5e7eb'
          }}>
            <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '20px' }}>
              Recent Threats
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {recentThreats.map((threat) => (
                <div key={threat.id} style={{
                  padding: '16px',
                  backgroundColor: '#f9fafb',
                  borderRadius: '8px',
                  border: '1px solid #e5e7eb'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                    <div>
                      <p style={{ fontSize: '14px', fontWeight: '500', color: '#111827', margin: '0 0 4px 0' }}>
                        {threat.subject}
                      </p>
                      <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>
                        From: {threat.sender}
                      </p>
                    </div>
                    <span style={{
                      padding: '4px 8px',
                      backgroundColor: getSeverityColor(threat.severity),
                      color: 'white',
                      fontSize: '10px',
                      fontWeight: '600',
                      borderRadius: '4px'
                    }}>
                      {threat.severity}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontSize: '12px', color: '#6b7280' }}>
                      {threat.time}
                    </span>
                    <span style={{
                      fontSize: '12px',
                      fontWeight: '500',
                      color: threat.status === 'Blocked' ? '#16a34a' : 
                             threat.status === 'Quarantined' ? '#f59e0b' : '#6b7280'
                    }}>
                      {threat.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          border: '1px solid #e5e7eb'
        }}>
          <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '20px' }}>
            Quick Actions
          </h2>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button style={{
              backgroundColor: '#2563eb',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '12px 20px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              🔍 Scan New Emails
            </button>
            
            <button style={{
              backgroundColor: '#16a34a',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '12px 20px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              🔒 View Quarantine
            </button>
            
            <button style={{
              backgroundColor: '#7c3aed',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '12px 20px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              📊 Generate Report
            </button>
            
            <button style={{
              backgroundColor: '#f59e0b',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '12px 20px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              ⚙️ Configure Rules
            </button>
          </div>
        </div>
      </div>

      {/* Add CSS for spinner animation */}
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
}

export default AdvancedDashboard;
