import React from 'react';

function Dashboard() {
  return (
    <div style={{ 
      minHeight: '100vh', 
      backgroundColor: '#f9fafb', 
      padding: '20px',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto',
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '24px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
      }}>
        <h1 style={{ 
          fontSize: '24px', 
          fontWeight: 'bold', 
          color: '#111827',
          marginBottom: '16px'
        }}>
          🛡️ Email Security Dashboard
        </h1>
        
        <p style={{ 
          color: '#6b7280', 
          marginBottom: '24px' 
        }}>
          Monitor and manage your email security in real-time
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '16px',
          marginBottom: '24px'
        }}>
          <div style={{
            backgroundColor: '#eff6ff',
            border: '1px solid #dbeafe',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <h3 style={{ fontWeight: '600', color: '#1e40af', marginBottom: '8px' }}>
              Emails Scanned
            </h3>
            <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#111827' }}>
              1,234
            </p>
            <p style={{ fontSize: '14px', color: '#16a34a' }}>
              +12% from yesterday
            </p>
          </div>

          <div style={{
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <h3 style={{ fontWeight: '600', color: '#dc2626', marginBottom: '8px' }}>
              Threats Detected
            </h3>
            <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#111827' }}>
              23
            </p>
            <p style={{ fontSize: '14px', color: '#dc2626' }}>
              +5% from yesterday
            </p>
          </div>

          <div style={{
            backgroundColor: '#f0fdf4',
            border: '1px solid #bbf7d0',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <h3 style={{ fontWeight: '600', color: '#16a34a', marginBottom: '8px' }}>
              Quarantined
            </h3>
            <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#111827' }}>
              8
            </p>
            <p style={{ fontSize: '14px', color: '#16a34a' }}>
              -2% from yesterday
            </p>
          </div>

          <div style={{
            backgroundColor: '#f8fafc',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            padding: '16px'
          }}>
            <h3 style={{ fontWeight: '600', color: '#475569', marginBottom: '8px' }}>
              Active Users
            </h3>
            <p style={{ fontSize: '24px', fontWeight: 'bold', color: '#111827' }}>
              156
            </p>
            <p style={{ fontSize: '14px', color: '#16a34a' }}>
              +3% from yesterday
            </p>
          </div>
        </div>

        <div style={{
          backgroundColor: '#f9fafb',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '24px'
        }}>
          <h2 style={{ 
            fontSize: '18px', 
            fontWeight: '600', 
            color: '#111827',
            marginBottom: '12px'
          }}>
            Recent Activity
          </h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '12px',
              padding: '8px',
              backgroundColor: 'white',
              borderRadius: '4px'
            }}>
              <div style={{ 
                width: '8px', 
                height: '8px', 
                backgroundColor: '#dc2626', 
                borderRadius: '50%' 
              }}></div>
              <span style={{ fontSize: '14px', color: '#111827' }}>
                Phishing attempt blocked - example@malicious.com
              </span>
              <span style={{ fontSize: '12px', color: '#6b7280', marginLeft: 'auto' }}>
                2 min ago
              </span>
            </div>
            
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '12px',
              padding: '8px',
              backgroundColor: 'white',
              borderRadius: '4px'
            }}>
              <div style={{ 
                width: '8px', 
                height: '8px', 
                backgroundColor: '#f59e0b', 
                borderRadius: '50%' 
              }}></div>
              <span style={{ fontSize: '14px', color: '#111827' }}>
                Suspicious email quarantined - invoice.pdf
              </span>
              <span style={{ fontSize: '12px', color: '#6b7280', marginLeft: 'auto' }}>
                5 min ago
              </span>
            </div>
            
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '12px',
              padding: '8px',
              backgroundColor: 'white',
              borderRadius: '4px'
            }}>
              <div style={{ 
                width: '8px', 
                height: '8px', 
                backgroundColor: '#10b981', 
                borderRadius: '50%' 
              }}></div>
              <span style={{ fontSize: '14px', color: '#111827' }}>
                Bulk email scan completed - 1,234 emails processed
              </span>
              <span style={{ fontSize: '12px', color: '#6b7280', marginLeft: 'auto' }}>
                10 min ago
              </span>
            </div>
          </div>
        </div>

        <div style={{ 
          display: 'flex',
          gap: '12px',
          flexWrap: 'wrap'
        }}>
          <button style={{
            backgroundColor: '#2563eb',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            padding: '8px 16px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer'
          }}>
            Scan New Emails
          </button>
          
          <button style={{
            backgroundColor: '#16a34a',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            padding: '8px 16px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer'
          }}>
            View Quarantine
          </button>
          
          <button style={{
            backgroundColor: '#7c3aed',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            padding: '8px 16px',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer'
          }}>
            Generate Report
          </button>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
