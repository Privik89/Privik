import React from 'react';

function EmailAnalysis() {
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
          📧 Email Analysis
        </h1>
        
        <p style={{ 
          color: '#6b7280', 
          marginBottom: '24px' 
        }}>
          Analyze and monitor email traffic for threats and anomalies
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
          gap: '20px',
          marginBottom: '24px'
        }}>
          <div style={{
            backgroundColor: '#eff6ff',
            border: '1px solid #dbeafe',
            borderRadius: '8px',
            padding: '20px'
          }}>
            <h3 style={{ fontWeight: '600', color: '#1e40af', marginBottom: '12px' }}>
              Real-time Scanning
            </h3>
            <p style={{ fontSize: '14px', color: '#374151', marginBottom: '16px' }}>
              Monitor emails as they arrive in real-time
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ 
                width: '8px', 
                height: '8px', 
                backgroundColor: '#16a34a', 
                borderRadius: '50%' 
              }}></div>
              <span style={{ fontSize: '12px', color: '#16a34a', fontWeight: '500' }}>
                Active - 1,234 emails/hour
              </span>
            </div>
          </div>

          <div style={{
            backgroundColor: '#fef2f2',
            border: '1px solid #fecaca',
            borderRadius: '8px',
            padding: '20px'
          }}>
            <h3 style={{ fontWeight: '600', color: '#dc2626', marginBottom: '12px' }}>
              Threat Detection
            </h3>
            <p style={{ fontSize: '14px', color: '#374151', marginBottom: '16px' }}>
              AI-powered threat identification and classification
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ 
                width: '8px', 
                height: '8px', 
                backgroundColor: '#dc2626', 
                borderRadius: '50%' 
              }}></div>
              <span style={{ fontSize: '12px', color: '#dc2626', fontWeight: '500' }}>
                23 threats detected today
              </span>
            </div>
          </div>

          <div style={{
            backgroundColor: '#f0fdf4',
            border: '1px solid #bbf7d0',
            borderRadius: '8px',
            padding: '20px'
          }}>
            <h3 style={{ fontWeight: '600', color: '#16a34a', marginBottom: '12px' }}>
              Content Analysis
            </h3>
            <p style={{ fontSize: '14px', color: '#374151', marginBottom: '16px' }}>
              Deep content inspection and behavioral analysis
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ 
                width: '8px', 
                height: '8px', 
                backgroundColor: '#16a34a', 
                borderRadius: '50%' 
              }}></div>
              <span style={{ fontSize: '12px', color: '#16a34a', fontWeight: '500' }}>
                99.2% accuracy rate
              </span>
            </div>
          </div>

          <div style={{
            backgroundColor: '#fef3c7',
            border: '1px solid #fde68a',
            borderRadius: '8px',
            padding: '20px'
          }}>
            <h3 style={{ fontWeight: '600', color: '#d97706', marginBottom: '12px' }}>
              Attachment Scanning
            </h3>
            <p style={{ fontSize: '14px', color: '#374151', marginBottom: '16px' }}>
              Safe attachment analysis and sandboxing
            </p>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ 
                width: '8px', 
                height: '8px', 
                backgroundColor: '#f59e0b', 
                borderRadius: '50%' 
              }}></div>
              <span style={{ fontSize: '12px', color: '#d97706', fontWeight: '500' }}>
                456 files scanned today
              </span>
            </div>
          </div>
        </div>

        <div style={{
          backgroundColor: '#f9fafb',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '20px'
        }}>
          <h2 style={{ 
            fontSize: '18px', 
            fontWeight: '600', 
            color: '#111827',
            marginBottom: '16px'
          }}>
            Recent Email Analysis
          </h2>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between',
              padding: '12px',
              backgroundColor: 'white',
              borderRadius: '6px',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ 
                  width: '8px', 
                  height: '8px', 
                  backgroundColor: '#dc2626', 
                  borderRadius: '50%' 
                }}></div>
                <div>
                  <p style={{ fontSize: '14px', fontWeight: '500', color: '#111827', margin: '0 0 2px 0' }}>
                    Phishing email detected
                  </p>
                  <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>
                    From: suspicious@fake-bank.com
                  </p>
                </div>
              </div>
              <span style={{ fontSize: '12px', color: '#6b7280' }}>
                2 min ago
              </span>
            </div>
            
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between',
              padding: '12px',
              backgroundColor: 'white',
              borderRadius: '6px',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ 
                  width: '8px', 
                  height: '8px', 
                  backgroundColor: '#f59e0b', 
                  borderRadius: '50%' 
                }}></div>
                <div>
                  <p style={{ fontSize: '14px', fontWeight: '500', color: '#111827', margin: '0 0 2px 0' }}>
                    Suspicious attachment quarantined
                  </p>
                  <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>
                    File: invoice_urgent.pdf
                  </p>
                </div>
              </div>
              <span style={{ fontSize: '12px', color: '#6b7280' }}>
                5 min ago
              </span>
            </div>
            
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between',
              padding: '12px',
              backgroundColor: 'white',
              borderRadius: '6px',
              border: '1px solid #e5e7eb'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <div style={{ 
                  width: '8px', 
                  height: '8px', 
                  backgroundColor: '#16a34a', 
                  borderRadius: '50%' 
                }}></div>
                <div>
                  <p style={{ fontSize: '14px', fontWeight: '500', color: '#111827', margin: '0 0 2px 0' }}>
                    Bulk email scan completed
                  </p>
                  <p style={{ fontSize: '12px', color: '#6b7280', margin: 0 }}>
                    1,234 emails processed successfully
                  </p>
                </div>
              </div>
              <span style={{ fontSize: '12px', color: '#6b7280' }}>
                10 min ago
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EmailAnalysis;
