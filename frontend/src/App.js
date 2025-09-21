import React, { useState } from 'react';
import Navigation from './components/Navigation';
import AdvancedDashboard from './components/AdvancedDashboard';
import EmailSearch from './components/EmailSearch';
import EnhancedSettings from './components/EnhancedSettings';
import { ToastContainer, useToast } from './components/Toast';
import './index.css';

function App() {
  const [currentPage, setCurrentPage] = useState('dashboard');
  const { toasts, removeToast } = useToast();

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <AdvancedDashboard />;
      case 'emails':
        return <EmailSearch />;
      case 'threats':
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
              <h1 style={{ fontSize: '24px', fontWeight: 'bold', color: '#111827', marginBottom: '16px' }}>
                🛡️ Threat Intelligence
              </h1>
              <p style={{ color: '#6b7280', marginBottom: '24px' }}>
                Monitor and analyze security threats
              </p>
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <p style={{ color: '#6b7280' }}>Threat Intelligence features coming soon...</p>
              </div>
            </div>
          </div>
        );
      case 'incidents':
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
              <h1 style={{ fontSize: '24px', fontWeight: 'bold', color: '#111827', marginBottom: '16px' }}>
                ⚠️ Security Incidents
              </h1>
              <p style={{ color: '#6b7280', marginBottom: '24px' }}>
                Manage and track security incidents
              </p>
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <p style={{ color: '#6b7280' }}>Incident management features coming soon...</p>
              </div>
            </div>
          </div>
        );
      case 'users':
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
              <h1 style={{ fontSize: '24px', fontWeight: 'bold', color: '#111827', marginBottom: '16px' }}>
                👥 User Risk Assessment
              </h1>
              <p style={{ color: '#6b7280', marginBottom: '24px' }}>
                Monitor user behavior and risk levels
              </p>
              <div style={{ textAlign: 'center', padding: '40px' }}>
                <p style={{ color: '#6b7280' }}>User risk management features coming soon...</p>
              </div>
            </div>
          </div>
        );
      case 'settings':
        return <EnhancedSettings />;
      default:
        return <AdvancedDashboard />;
    }
  };

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Navigation currentPage={currentPage} onPageChange={setCurrentPage} />
      <div style={{ 
        flex: 1, 
        marginLeft: '250px',
        minHeight: '100vh'
      }}>
        {renderPage()}
      </div>
      <ToastContainer toasts={toasts} onRemoveToast={removeToast} />
    </div>
  );
}

export default App;