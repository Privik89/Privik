import React, { useState, useEffect, useCallback } from 'react';

// Toast notification component
export const Toast = ({ message, type = 'info', duration = 5000, onClose }) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isLeaving, setIsLeaving] = useState(false);

  const handleClose = useCallback(() => {
    setIsLeaving(true);
    setTimeout(() => {
      setIsVisible(false);
      onClose?.();
    }, 300);
  }, [onClose]);

  useEffect(() => {
    const timer = setTimeout(() => {
      handleClose();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, handleClose]);

  if (!isVisible) return null;

  const getToastStyle = () => {
    const baseStyle = {
      position: 'fixed',
      top: '20px',
      right: '20px',
      minWidth: '300px',
      maxWidth: '400px',
      padding: '16px 20px',
      borderRadius: '8px',
      boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
      zIndex: 9999,
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      transform: isLeaving ? 'translateX(100%)' : 'translateX(0)',
      transition: 'transform 0.3s ease-in-out',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    };

    switch (type) {
      case 'success':
        return {
          ...baseStyle,
          backgroundColor: '#f0fdf4',
          border: '1px solid #bbf7d0',
          color: '#166534'
        };
      case 'error':
        return {
          ...baseStyle,
          backgroundColor: '#fef2f2',
          border: '1px solid #fecaca',
          color: '#991b1b'
        };
      case 'warning':
        return {
          ...baseStyle,
          backgroundColor: '#fffbeb',
          border: '1px solid #fed7aa',
          color: '#92400e'
        };
      case 'info':
      default:
        return {
          ...baseStyle,
          backgroundColor: '#eff6ff',
          border: '1px solid #bfdbfe',
          color: '#1e40af'
        };
    }
  };

  const getIcon = () => {
    switch (type) {
      case 'success': return '✅';
      case 'error': return '❌';
      case 'warning': return '⚠️';
      case 'info':
      default: return 'ℹ️';
    }
  };

  return (
    <div style={getToastStyle()}>
      <span style={{ fontSize: '18px' }}>{getIcon()}</span>
      <div style={{ flex: 1 }}>
        <p style={{ margin: 0, fontSize: '14px', fontWeight: '500' }}>
          {message}
        </p>
      </div>
      <button
        onClick={handleClose}
        style={{
          background: 'none',
          border: 'none',
          fontSize: '16px',
          cursor: 'pointer',
          color: 'inherit',
          opacity: 0.7,
          padding: '4px'
        }}
      >
        ×
      </button>
    </div>
  );
};

// Toast container component
export const ToastContainer = ({ toasts, onRemoveToast }) => {
  return (
    <div style={{ position: 'fixed', top: 0, right: 0, zIndex: 9999 }}>
      {toasts.map((toast, index) => (
        <div key={toast.id} style={{ marginBottom: '8px' }}>
          <Toast
            message={toast.message}
            type={toast.type}
            duration={toast.duration}
            onClose={() => onRemoveToast(toast.id)}
          />
        </div>
      ))}
    </div>
  );
};

// Hook for managing toasts
export const useToast = () => {
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = 'info', duration = 5000) => {
    const id = Date.now() + Math.random();
    const newToast = { id, message, type, duration };
    
    setToasts(prev => [...prev, newToast]);
    
    // Auto-remove after duration
    setTimeout(() => {
      removeToast(id);
    }, duration);
  };

  const removeToast = (id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  };

  const success = (message, duration) => addToast(message, 'success', duration);
  const error = (message, duration) => addToast(message, 'error', duration);
  const warning = (message, duration) => addToast(message, 'warning', duration);
  const info = (message, duration) => addToast(message, 'info', duration);

  return {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    warning,
    info
  };
};
