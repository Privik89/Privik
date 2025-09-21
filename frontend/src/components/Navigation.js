import React from 'react';

function Navigation({ currentPage, onPageChange }) {
  const menuItems = [
    { id: 'dashboard', name: 'Dashboard', icon: '🏠' },
    { id: 'emails', name: 'Email Analysis', icon: '📧' },
    { id: 'threats', name: 'Threat Intelligence', icon: '🛡️' },
    { id: 'incidents', name: 'Incidents', icon: '⚠️' },
    { id: 'users', name: 'User Risk', icon: '👥' },
    { id: 'settings', name: 'Settings', icon: '⚙️' },
  ];

  return (
    <div style={{
      position: 'fixed',
      left: 0,
      top: 0,
      width: '250px',
      height: '100vh',
      backgroundColor: 'white',
      borderRight: '1px solid #e5e7eb',
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
      zIndex: 1000
    }}>
      {/* Logo */}
      <div style={{
        padding: '20px',
        borderBottom: '1px solid #e5e7eb',
        textAlign: 'center'
      }}>
        <h1 style={{
          fontSize: '20px',
          fontWeight: 'bold',
          color: '#2563eb',
          margin: 0
        }}>
          🛡️ Privik
        </h1>
        <p style={{
          fontSize: '12px',
          color: '#6b7280',
          margin: '4px 0 0 0'
        }}>
          Email Security Platform
        </p>
      </div>

      {/* Navigation Menu */}
      <nav style={{ padding: '16px 0' }}>
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => onPageChange(item.id)}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '12px 20px',
              border: 'none',
              backgroundColor: currentPage === item.id ? '#eff6ff' : 'transparent',
              color: currentPage === item.id ? '#2563eb' : '#374151',
              fontSize: '14px',
              fontWeight: currentPage === item.id ? '500' : '400',
              cursor: 'pointer',
              transition: 'all 0.2s',
              textAlign: 'left'
            }}
          >
            <span style={{ fontSize: '16px' }}>{item.icon}</span>
            {item.name}
          </button>
        ))}
      </nav>

      {/* Footer */}
      <div style={{
        position: 'absolute',
        bottom: '20px',
        left: '20px',
        right: '20px',
        padding: '16px',
        backgroundColor: '#f9fafb',
        borderRadius: '8px',
        border: '1px solid #e5e7eb'
      }}>
        <div style={{
          fontSize: '12px',
          color: '#6b7280',
          textAlign: 'center'
        }}>
          <p style={{ margin: '0 0 4px 0' }}>Privik v1.0.0</p>
          <p style={{ margin: 0 }}>Status: 🟢 Online</p>
        </div>
      </div>
    </div>
  );
}

export default Navigation;
