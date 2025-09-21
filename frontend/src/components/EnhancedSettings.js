import React, { useState, useEffect } from 'react';
import { useSettings } from '../hooks/useApi';
import { useToast } from './Toast';
import { LoadingSpinner, SkeletonLoader } from './LoadingSpinner';

function EnhancedSettings() {
  const [activeTab, setActiveTab] = useState('general');
  const [formData, setFormData] = useState({});
  const [isDirty, setIsDirty] = useState(false);
  const [validationErrors, setValidationErrors] = useState({});
  
  const { settings, updateSettings, loading, error: settingsError } = useSettings();
  const { success, error: showError } = useToast();

  const tabs = [
    { id: 'general', name: 'General', icon: '⚙️' },
    { id: 'security', name: 'Security', icon: '🔒' },
    { id: 'notifications', name: 'Notifications', icon: '🔔' },
    { id: 'users', name: 'Users', icon: '👥' },
  ];

  // Initialize form data when settings are loaded
  useEffect(() => {
    if (settings) {
      setFormData(settings);
    }
  }, [settings]);

  // Track form changes
  const handleInputChange = (field, value) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
    setIsDirty(true);
    
    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors(prev => ({
        ...prev,
        [field]: null
      }));
    }
  };

  // Form validation
  const validateForm = () => {
    const errors = {};
    
    if (formData.platformName && formData.platformName.length < 3) {
      errors.platformName = 'Platform name must be at least 3 characters';
    }
    
    if (formData.adminEmail && !/\S+@\S+\.\S+/.test(formData.adminEmail)) {
      errors.adminEmail = 'Please enter a valid email address';
    }
    
    if (formData.sessionTimeout && (formData.sessionTimeout < 5 || formData.sessionTimeout > 480)) {
      errors.sessionTimeout = 'Session timeout must be between 5 and 480 minutes';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Save settings
  const handleSave = async () => {
    if (!validateForm()) {
      showError('Please fix the validation errors before saving');
      return;
    }

    try {
      await updateSettings(formData);
      setIsDirty(false);
      success('Settings saved successfully!');
    } catch (err) {
      showError('Failed to save settings. Please try again.');
    }
  };

  // Reset form
  const handleReset = () => {
    setFormData(settings || {});
    setIsDirty(false);
    setValidationErrors({});
  };

  const renderGeneralTab = () => (
    <div>
      <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '20px' }}>
        General Settings
      </h2>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div>
          <label style={{ 
            display: 'block', 
            fontSize: '14px', 
            fontWeight: '500', 
            color: '#374151', 
            marginBottom: '6px' 
          }}>
            Platform Name *
          </label>
          <input
            type="text"
            value={formData.platformName || ''}
            onChange={(e) => handleInputChange('platformName', e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              border: validationErrors.platformName ? '1px solid #dc2626' : '1px solid #d1d5db',
              borderRadius: '8px',
              fontSize: '14px',
              backgroundColor: 'white'
            }}
            placeholder="Enter platform name"
          />
          {validationErrors.platformName && (
            <p style={{ fontSize: '12px', color: '#dc2626', margin: '4px 0 0 0' }}>
              {validationErrors.platformName}
            </p>
          )}
        </div>

        <div>
          <label style={{ 
            display: 'block', 
            fontSize: '14px', 
            fontWeight: '500', 
            color: '#374151', 
            marginBottom: '6px' 
          }}>
            Admin Email *
          </label>
          <input
            type="email"
            value={formData.adminEmail || ''}
            onChange={(e) => handleInputChange('adminEmail', e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              border: validationErrors.adminEmail ? '1px solid #dc2626' : '1px solid #d1d5db',
              borderRadius: '8px',
              fontSize: '14px',
              backgroundColor: 'white'
            }}
            placeholder="admin@company.com"
          />
          {validationErrors.adminEmail && (
            <p style={{ fontSize: '12px', color: '#dc2626', margin: '4px 0 0 0' }}>
              {validationErrors.adminEmail}
            </p>
          )}
        </div>

        <div>
          <label style={{ 
            display: 'block', 
            fontSize: '14px', 
            fontWeight: '500', 
            color: '#374151', 
            marginBottom: '6px' 
          }}>
            Default Language
          </label>
          <select
            value={formData.defaultLanguage || 'en'}
            onChange={(e) => handleInputChange('defaultLanguage', e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              fontSize: '14px',
              backgroundColor: 'white'
            }}
          >
            <option value="en">English</option>
            <option value="es">Spanish</option>
            <option value="fr">French</option>
            <option value="de">German</option>
          </select>
        </div>

        <div>
          <label style={{ 
            display: 'block', 
            fontSize: '14px', 
            fontWeight: '500', 
            color: '#374151', 
            marginBottom: '6px' 
          }}>
            Timezone
          </label>
          <select
            value={formData.timezone || 'UTC'}
            onChange={(e) => handleInputChange('timezone', e.target.value)}
            style={{
              width: '100%',
              padding: '12px',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              fontSize: '14px',
              backgroundColor: 'white'
            }}
          >
            <option value="UTC">UTC</option>
            <option value="America/New_York">Eastern Time</option>
            <option value="America/Chicago">Central Time</option>
            <option value="America/Denver">Mountain Time</option>
            <option value="America/Los_Angeles">Pacific Time</option>
            <option value="Europe/London">London</option>
            <option value="Europe/Paris">Paris</option>
            <option value="Asia/Tokyo">Tokyo</option>
          </select>
        </div>
      </div>
    </div>
  );

  const renderSecurityTab = () => (
    <div>
      <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '20px' }}>
        Security Settings
      </h2>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{
          padding: '20px',
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
          border: '1px solid #e5e7eb'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '12px'
          }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '500', color: '#111827', margin: '0 0 4px 0' }}>
                Two-Factor Authentication
              </h3>
              <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
                Require 2FA for all admin accounts
              </p>
            </div>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={formData.enable2FA || false}
                onChange={(e) => handleInputChange('enable2FA', e.target.checked)}
                style={{ marginRight: '8px' }}
              />
              <span style={{ fontSize: '14px', color: '#374151' }}>
                {formData.enable2FA ? 'Enabled' : 'Disabled'}
              </span>
            </label>
          </div>
        </div>

        <div>
          <label style={{ 
            display: 'block', 
            fontSize: '14px', 
            fontWeight: '500', 
            color: '#374151', 
            marginBottom: '6px' 
          }}>
            Session Timeout (minutes) *
          </label>
          <input
            type="number"
            min="5"
            max="480"
            value={formData.sessionTimeout || 30}
            onChange={(e) => handleInputChange('sessionTimeout', parseInt(e.target.value))}
            style={{
              width: '100%',
              padding: '12px',
              border: validationErrors.sessionTimeout ? '1px solid #dc2626' : '1px solid #d1d5db',
              borderRadius: '8px',
              fontSize: '14px',
              backgroundColor: 'white'
            }}
          />
          {validationErrors.sessionTimeout && (
            <p style={{ fontSize: '12px', color: '#dc2626', margin: '4px 0 0 0' }}>
              {validationErrors.sessionTimeout}
            </p>
          )}
        </div>

        <div style={{
          padding: '20px',
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
          border: '1px solid #e5e7eb'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '12px'
          }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '500', color: '#111827', margin: '0 0 4px 0' }}>
                Password Policy
              </h3>
              <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
                Enforce strong password requirements
              </p>
            </div>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={formData.enforcePasswordPolicy || false}
                onChange={(e) => handleInputChange('enforcePasswordPolicy', e.target.checked)}
                style={{ marginRight: '8px' }}
              />
              <span style={{ fontSize: '14px', color: '#374151' }}>
                {formData.enforcePasswordPolicy ? 'Enabled' : 'Disabled'}
              </span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );

  const renderNotificationsTab = () => (
    <div>
      <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '20px' }}>
        Notification Settings
      </h2>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{
          padding: '20px',
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
          border: '1px solid #e5e7eb'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '12px'
          }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '500', color: '#111827', margin: '0 0 4px 0' }}>
                Email Notifications
              </h3>
              <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
                Send notifications via email
              </p>
            </div>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={formData.enableEmailNotifications || false}
                onChange={(e) => handleInputChange('enableEmailNotifications', e.target.checked)}
                style={{ marginRight: '8px' }}
              />
              <span style={{ fontSize: '14px', color: '#374151' }}>
                {formData.enableEmailNotifications ? 'Enabled' : 'Disabled'}
              </span>
            </label>
          </div>
        </div>

        <div style={{
          padding: '20px',
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
          border: '1px solid #e5e7eb'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '12px'
          }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '500', color: '#111827', margin: '0 0 4px 0' }}>
                SMS Notifications
              </h3>
              <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
                Send critical alerts via SMS
              </p>
            </div>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={formData.enableSMSNotifications || false}
                onChange={(e) => handleInputChange('enableSMSNotifications', e.target.checked)}
                style={{ marginRight: '8px' }}
              />
              <span style={{ fontSize: '14px', color: '#374151' }}>
                {formData.enableSMSNotifications ? 'Enabled' : 'Disabled'}
              </span>
            </label>
          </div>
        </div>

        <div style={{
          padding: '20px',
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
          border: '1px solid #e5e7eb'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '12px'
          }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '500', color: '#111827', margin: '0 0 4px 0' }}>
                Push Notifications
              </h3>
              <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
                Send real-time push notifications
              </p>
            </div>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={formData.enablePushNotifications || false}
                onChange={(e) => handleInputChange('enablePushNotifications', e.target.checked)}
                style={{ marginRight: '8px' }}
              />
              <span style={{ fontSize: '14px', color: '#374151' }}>
                {formData.enablePushNotifications ? 'Enabled' : 'Disabled'}
              </span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );

  const renderUsersTab = () => (
    <div>
      <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '20px' }}>
        User Management
      </h2>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div style={{
          padding: '20px',
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
          border: '1px solid #e5e7eb'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '12px'
          }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '500', color: '#111827', margin: '0 0 4px 0' }}>
                Total Users
              </h3>
              <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
                156 active users
              </p>
            </div>
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
              View All
            </button>
          </div>
        </div>

        <div style={{
          padding: '20px',
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
          border: '1px solid #e5e7eb'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '12px'
          }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '500', color: '#111827', margin: '0 0 4px 0' }}>
                Admin Users
              </h3>
              <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
                5 administrator accounts
              </p>
            </div>
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
              Manage
            </button>
          </div>
        </div>

        <div style={{
          padding: '20px',
          backgroundColor: '#f9fafb',
          borderRadius: '8px',
          border: '1px solid #e5e7eb'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '12px'
          }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '500', color: '#111827', margin: '0 0 4px 0' }}>
                User Registration
              </h3>
              <p style={{ fontSize: '14px', color: '#6b7280', margin: 0 }}>
                Allow new user registrations
              </p>
            </div>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={formData.allowUserRegistration || false}
                onChange={(e) => handleInputChange('allowUserRegistration', e.target.checked)}
                style={{ marginRight: '8px' }}
              />
              <span style={{ fontSize: '14px', color: '#374151' }}>
                {formData.allowUserRegistration ? 'Enabled' : 'Disabled'}
              </span>
            </label>
          </div>
        </div>
      </div>
    </div>
  );

  const renderTabContent = () => {
    switch (activeTab) {
      case 'general': return renderGeneralTab();
      case 'security': return renderSecurityTab();
      case 'notifications': return renderNotificationsTab();
      case 'users': return renderUsersTab();
      default: return renderGeneralTab();
    }
  };

  if (loading && !settings) {
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
          <SkeletonLoader width="200px" height="32px" lines={1} />
          <div style={{ marginTop: '24px' }}>
            <SkeletonLoader width="100%" height="60px" lines={4} />
          </div>
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
        maxWidth: '1200px',
        margin: '0 auto',
        backgroundColor: 'white',
        borderRadius: '8px',
        padding: '24px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '24px'
        }}>
        <h1 style={{ 
          fontSize: '24px', 
          fontWeight: 'bold', 
          color: '#111827',
          margin: 0
        }}>
          ⚙️ Enhanced Settings
        </h1>
        
        {/* Settings Error Display */}
        {settingsError && (
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
                Settings Error
              </p>
              <p style={{ fontSize: '12px', color: '#991b1b', margin: 0 }}>
                {settingsError} - Some settings may not be available.
              </p>
            </div>
          </div>
        )}
          
          {isDirty && (
            <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
              <span style={{ fontSize: '12px', color: '#f59e0b' }}>
                • Unsaved changes
              </span>
              <button
                onClick={handleReset}
                style={{
                  padding: '8px 16px',
                  backgroundColor: 'transparent',
                  color: '#6b7280',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  cursor: 'pointer'
                }}
              >
                Reset
              </button>
              <button
                onClick={handleSave}
                disabled={loading}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#16a34a',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: loading ? 'not-allowed' : 'pointer',
                  opacity: loading ? 0.7 : 1,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
              >
                {loading && <LoadingSpinner size="small" color="white" />}
                Save Changes
              </button>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div style={{
          borderBottom: '1px solid #e5e7eb',
          marginBottom: '24px'
        }}>
          <div style={{ display: 'flex', gap: '0' }}>
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  padding: '12px 24px',
                  border: 'none',
                  backgroundColor: activeTab === tab.id ? '#2563eb' : 'transparent',
                  color: activeTab === tab.id ? 'white' : '#6b7280',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                  borderBottom: activeTab === tab.id ? '2px solid #2563eb' : '2px solid transparent',
                  transition: 'all 0.2s',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}
              >
                <span>{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </div>
        </div>

        {/* Tab Content */}
        {renderTabContent()}
      </div>
    </div>
  );
}

export default EnhancedSettings;
