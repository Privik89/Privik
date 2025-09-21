import React from 'react';

// Loading spinner component with different sizes and styles
export const LoadingSpinner = ({ 
  size = 'medium', 
  color = '#2563eb', 
  text = null,
  overlay = false 
}) => {
  const getSize = () => {
    switch (size) {
      case 'small': return '20px';
      case 'large': return '48px';
      case 'xlarge': return '64px';
      case 'medium':
      default: return '32px';
    }
  };

  const spinnerStyle = {
    width: getSize(),
    height: getSize(),
    border: `3px solid #e5e7eb`,
    borderTop: `3px solid ${color}`,
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
    margin: '0 auto'
  };

  const containerStyle = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    padding: text ? '20px' : '10px'
  };

  const overlayStyle = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255, 255, 255, 0.8)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 9998
  };

  const content = (
    <div style={containerStyle}>
      <div style={spinnerStyle}></div>
      {text && (
        <p style={{
          margin: 0,
          fontSize: '14px',
          color: '#6b7280',
          fontWeight: '500'
        }}>
          {text}
        </p>
      )}
    </div>
  );

  if (overlay) {
    return (
      <>
        <div style={overlayStyle}>
          {content}
        </div>
        <style>
          {`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}
        </style>
      </>
    );
  }

  return (
    <>
      {content}
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </>
  );
};

// Button loading state
export const LoadingButton = ({ 
  loading = false, 
  children, 
  disabled = false,
  onClick,
  style = {},
  ...props 
}) => {
  const buttonStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    opacity: loading ? 0.7 : 1,
    cursor: loading || disabled ? 'not-allowed' : 'pointer',
    ...style
  };

  return (
    <button
      {...props}
      onClick={onClick}
      disabled={loading || disabled}
      style={buttonStyle}
    >
      {loading && <LoadingSpinner size="small" color="currentColor" />}
      {children}
    </button>
  );
};

// Inline loading indicator
export const InlineLoader = ({ text = 'Loading...' }) => {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      fontSize: '14px',
      color: '#6b7280'
    }}>
      <LoadingSpinner size="small" />
      <span>{text}</span>
    </div>
  );
};

// Skeleton loader for content
export const SkeletonLoader = ({ width = '100%', height = '20px', lines = 1 }) => {
  const skeletonStyle = {
    backgroundColor: '#e5e7eb',
    borderRadius: '4px',
    animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
    marginBottom: lines > 1 ? '8px' : '0'
  };

  return (
    <>
      {Array.from({ length: lines }, (_, index) => (
        <div
          key={index}
          style={{
            ...skeletonStyle,
            width: index === lines - 1 ? '75%' : width,
            height
          }}
        />
      ))}
      <style>
        {`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }
        `}
      </style>
    </>
  );
};
