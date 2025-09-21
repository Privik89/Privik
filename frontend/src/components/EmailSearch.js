import React, { useState } from 'react';
import { useEmailSearch } from '../hooks/useApi';

function EmailSearch() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilter, setSelectedFilter] = useState('all');
  const [selectedDateRange, setSelectedDateRange] = useState('today');
  
  // Use the API hook for email search
  const { results: searchResults, totalCount, search, clearResults, loading: isSearching, error: searchError } = useEmailSearch();

  const filters = [
    { value: 'all', label: 'All Emails' },
    { value: 'threats', label: 'Threats Only' },
    { value: 'quarantined', label: 'Quarantined' },
    { value: 'blocked', label: 'Blocked' },
    { value: 'safe', label: 'Safe Emails' }
  ];

  const dateRanges = [
    { value: 'today', label: 'Today' },
    { value: 'yesterday', label: 'Yesterday' },
    { value: 'week', label: 'This Week' },
    { value: 'month', label: 'This Month' },
    { value: 'custom', label: 'Custom Range' }
  ];

  // Mock search results (for fallback when API is unavailable)
  // const mockResults = [
  //   {
  //     id: 1,
  //     subject: 'Urgent: Verify Your Account',
  //     sender: 'suspicious@fake-bank.com',
  //     recipient: 'user@company.com',
  //     timestamp: '2024-01-15 14:30:25',
  //     status: 'blocked',
  //     threatType: 'phishing',
  //     severity: 'high',
  //     size: '2.3 KB'
  //   },
  //   // ... other mock results
  // ];

  const handleSearch = async () => {
    try {
      await search(searchQuery, {
        status: selectedFilter,
        dateRange: selectedDateRange
      });
    } catch (err) {
      console.error('Search failed:', err);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'blocked': return '#dc2626';
      case 'quarantined': return '#f59e0b';
      case 'safe': return '#16a34a';
      default: return '#6b7280';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return '#dc2626';
      case 'high': return '#f59e0b';
      case 'medium': return '#eab308';
      case 'low': return '#16a34a';
      default: return '#6b7280';
    }
  };

  const getThreatTypeIcon = (threatType) => {
    switch (threatType) {
      case 'phishing': return '🎣';
      case 'malware': return '🦠';
      case 'spam': return '📧';
      default: return '✅';
    }
  };

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
        {/* Header */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '24px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
          border: '1px solid #e5e7eb',
          marginBottom: '24px'
        }}>
          <h1 style={{ 
            fontSize: '28px', 
            fontWeight: 'bold', 
            color: '#111827',
            marginBottom: '16px'
          }}>
            🔍 Email Search & Analysis
          </h1>
          
          {/* Search Bar */}
          <div style={{
            display: 'flex',
            gap: '12px',
            marginBottom: '20px',
            flexWrap: 'wrap'
          }}>
            <div style={{ flex: 1, minWidth: '300px' }}>
              <input
                type="text"
                placeholder="Search emails by subject, sender, or recipient..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  border: '1px solid #d1d5db',
                  borderRadius: '8px',
                  fontSize: '14px',
                  backgroundColor: 'white'
                }}
              />
            </div>
            
            <button
              onClick={handleSearch}
              disabled={isSearching}
              style={{
                padding: '12px 24px',
                backgroundColor: isSearching ? '#9ca3af' : '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: isSearching ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}
            >
              {isSearching ? '⏳ Searching...' : '🔍 Search'}
            </button>
          </div>

          {/* Filters */}
          <div style={{
            display: 'flex',
            gap: '16px',
            flexWrap: 'wrap',
            alignItems: 'center'
          }}>
            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '12px', 
                fontWeight: '500', 
                color: '#374151', 
                marginBottom: '4px' 
              }}>
                Filter by Status
              </label>
              <select
                value={selectedFilter}
                onChange={(e) => setSelectedFilter(e.target.value)}
                style={{
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: 'white'
                }}
              >
                {filters.map(filter => (
                  <option key={filter.value} value={filter.value}>
                    {filter.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label style={{ 
                display: 'block', 
                fontSize: '12px', 
                fontWeight: '500', 
                color: '#374151', 
                marginBottom: '4px' 
              }}>
                Date Range
              </label>
              <select
                value={selectedDateRange}
                onChange={(e) => setSelectedDateRange(e.target.value)}
                style={{
                  padding: '8px 12px',
                  border: '1px solid #d1d5db',
                  borderRadius: '6px',
                  fontSize: '14px',
                  backgroundColor: 'white'
                }}
              >
                {dateRanges.map(range => (
                  <option key={range.value} value={range.value}>
                    {range.label}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ marginLeft: 'auto' }}>
              <button
              onClick={() => {
                setSearchQuery('');
                setSelectedFilter('all');
                setSelectedDateRange('today');
                clearResults();
              }}
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
                Clear Filters
              </button>
            </div>
          </div>
        </div>

        {/* Error Display */}
        {searchError && (
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
                Search Error
              </p>
              <p style={{ fontSize: '12px', color: '#991b1b', margin: 0 }}>
                {searchError} - Please try again or check your connection.
              </p>
            </div>
          </div>
        )}

        {/* Search Results */}
        {searchResults.length > 0 && (
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '24px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            border: '1px solid #e5e7eb'
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '20px'
            }}>
            <h2 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', margin: 0 }}>
              Search Results ({searchResults.length}{totalCount > 0 ? ` of ${totalCount}` : ''})
            </h2>
              <button style={{
                padding: '8px 16px',
                backgroundColor: '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                fontSize: '14px',
                cursor: 'pointer'
              }}>
                Export Results
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {searchResults.map((email) => (
                <div key={email.id} style={{
                  padding: '16px',
                  backgroundColor: '#f9fafb',
                  borderRadius: '8px',
                  border: '1px solid #e5e7eb',
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'flex-start',
                    marginBottom: '12px'
                  }}>
                    <div style={{ flex: 1 }}>
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '12px',
                        marginBottom: '8px'
                      }}>
                        <span style={{ fontSize: '16px' }}>
                          {getThreatTypeIcon(email.threatType)}
                        </span>
                        <h3 style={{
                          fontSize: '16px',
                          fontWeight: '500',
                          color: '#111827',
                          margin: 0
                        }}>
                          {email.subject}
                        </h3>
                      </div>
                      
                      <div style={{
                        display: 'flex',
                        gap: '24px',
                        fontSize: '14px',
                        color: '#6b7280'
                      }}>
                        <span><strong>From:</strong> {email.sender}</span>
                        <span><strong>To:</strong> {email.recipient}</span>
                        <span><strong>Size:</strong> {email.size}</span>
                      </div>
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '8px' }}>
                      <span style={{
                        padding: '4px 8px',
                        backgroundColor: getStatusColor(email.status),
                        color: 'white',
                        fontSize: '10px',
                        fontWeight: '600',
                        borderRadius: '4px',
                        textTransform: 'uppercase'
                      }}>
                        {email.status}
                      </span>
                      
                      {email.severity !== 'low' && (
                        <span style={{
                          padding: '4px 8px',
                          backgroundColor: getSeverityColor(email.severity),
                          color: 'white',
                          fontSize: '10px',
                          fontWeight: '600',
                          borderRadius: '4px',
                          textTransform: 'uppercase'
                        }}>
                          {email.severity}
                        </span>
                      )}
                    </div>
                  </div>

                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    fontSize: '12px',
                    color: '#6b7280'
                  }}>
                    <span>{email.timestamp}</span>
                    <div style={{ display: 'flex', gap: '12px' }}>
                      <button style={{
                        padding: '4px 8px',
                        backgroundColor: 'transparent',
                        color: '#2563eb',
                        border: '1px solid #2563eb',
                        borderRadius: '4px',
                        fontSize: '12px',
                        cursor: 'pointer'
                      }}>
                        View Details
                      </button>
                      <button style={{
                        padding: '4px 8px',
                        backgroundColor: 'transparent',
                        color: '#16a34a',
                        border: '1px solid #16a34a',
                        borderRadius: '4px',
                        fontSize: '12px',
                        cursor: 'pointer'
                      }}>
                        Download
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* No Results */}
        {searchResults.length === 0 && !isSearching && (
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '40px',
            boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
            border: '1px solid #e5e7eb',
            textAlign: 'center'
          }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔍</div>
            <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#111827', marginBottom: '8px' }}>
              No emails found
            </h3>
            <p style={{ color: '#6b7280', marginBottom: '20px' }}>
              Try adjusting your search criteria or filters
            </p>
            <button
              onClick={handleSearch}
              style={{
                padding: '12px 24px',
                backgroundColor: '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '500',
                cursor: 'pointer'
              }}
            >
              Search All Emails
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default EmailSearch;
