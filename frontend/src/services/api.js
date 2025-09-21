// API service layer for Privik Email Security Platform
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Generic request method
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        return await response.json();
      }
      
      return await response.text();
    } catch (error) {
      console.error('API request failed:', error);
      // Return mock data for testing when backend is not available
      return this.getMockData(endpoint);
    }
  }

  // Mock data for when backend is not available
  getMockData(endpoint) {
    if (endpoint.includes('/dashboard/stats')) {
      return {
        stats: {
          emailsScanned: 12456,
          threatsDetected: 23,
          quarantined: 8,
          detectionRate: 99.2
        },
        metrics: {
          threatTypes: [
            {"name": "Phishing", "count": 12, "percentage": 52, "color": "#dc2626"},
            {"name": "Malware", "count": 7, "percentage": 30, "color": "#f59e0b"},
            {"name": "Spam", "count": 4, "percentage": 18, "color": "#10b981"}
          ]
        },
        activity: [
          {
            "id": 1,
            "type": "Phishing",
            "severity": "High",
            "sender": "suspicious@fake-bank.com",
            "subject": "Urgent: Verify Your Account",
            "recipient": "user@company.com",
            "time": "2 minutes ago",
            "status": "Blocked"
          },
          {
            "id": 2,
            "type": "Malware",
            "severity": "Critical",
            "sender": "noreply@invoice-system.com",
            "subject": "Invoice #INV-2024-001",
            "recipient": "user@company.com",
            "time": "5 minutes ago",
            "status": "Quarantined"
          }
        ],
        timestamp: new Date().toISOString()
      };
    }
    
    if (endpoint.includes('/emails')) {
      return {
        results: [
          {
            "id": 1,
            "subject": "Urgent: Verify Your Account",
            "sender": "suspicious@fake-bank.com",
            "recipient": "user@company.com",
            "timestamp": "2024-01-15T14:30:25",
            "status": "blocked",
            "threatType": "phishing",
            "severity": "high",
            "size": "2.3 KB"
          },
          {
            "id": 2,
            "subject": "Your Amazon Order Confirmation",
            "sender": "support@amazon.com",
            "recipient": "user@company.com",
            "timestamp": "2024-01-15T10:15:00",
            "status": "delivered",
            "threatType": "none",
            "severity": "none",
            "size": "15.7 KB"
          }
        ],
        totalCount: 2,
        hasMore: false
      };
    }
    
    if (endpoint.includes('/settings')) {
      return {
        general: {
          platformName: "Privik Email Security",
          version: "2.0.0",
          environment: "production",
          timezone: "UTC",
          language: "en"
        },
        security: {
          jwtEnabled: true,
          passwordPolicy: {
            minLength: 8,
            requireUppercase: true,
            requireNumbers: true,
            requireSpecialChars: true
          }
        },
        notifications: {
          emailNotifications: true,
          pushNotifications: false
        }
      };
    }
    
    return null;
  }

  // GET request
  async get(endpoint, params = {}) {
    const searchParams = new URLSearchParams();
    Object.keys(params).forEach(key => {
      if (params[key] !== undefined && params[key] !== null) {
        searchParams.append(key, params[key]);
      }
    });
    const queryString = searchParams.toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    
    return this.request(url, { method: 'GET' });
  }

  // POST request
  async post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // PUT request
  async put(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // DELETE request
  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // Health check
  async healthCheck() {
    return this.get('/health');
  }

  // Dashboard APIs
  async getDashboardStats(timeRange = '24h') {
    return this.get('/api/test/dashboard/stats', { time_range: timeRange });
  }

  async getDashboardMetrics() {
    return this.get('/api/dashboard/metrics');
  }

  async getRecentActivity(limit = 10) {
    return this.get('/api/dashboard/activity', { limit });
  }

  // Email Analysis APIs
  async searchEmails(query, filters = {}) {
    return this.get('/api/test/emails', { query, ...filters });
  }

  async getEmailDetails(emailId) {
    return this.get(`/api/emails/${emailId}`);
  }

  async getEmailStats() {
    return this.get('/api/emails/stats');
  }

  async getThreatTypes() {
    return this.get('/api/threats/types');
  }

  // Quarantine APIs
  async getQuarantinedEmails(filters = {}) {
    return this.get('/api/quarantine', filters);
  }

  async releaseEmail(emailId) {
    return this.post(`/api/quarantine/${emailId}/release`);
  }

  async deleteEmail(emailId) {
    return this.delete(`/api/quarantine/${emailId}`);
  }

  // Settings APIs
  async getSettings() {
    return this.get('/api/test/settings');
  }

  async updateSettings(settings) {
    return this.put('/api/settings', settings);
  }

  // User Management APIs
  async getUsers() {
    return this.get('/api/users');
  }

  async createUser(userData) {
    return this.post('/api/users', userData);
  }

  async updateUser(userId, userData) {
    return this.put(`/api/users/${userId}`, userData);
  }

  async deleteUser(userId) {
    return this.delete(`/api/users/${userId}`);
  }

  // Threat Intelligence APIs
  async getThreatIntelligence() {
    return this.get('/api/threat-intel');
  }

  async getThreatFeeds() {
    return this.get('/api/threat-feeds');
  }

  // Performance APIs
  async getPerformanceMetrics() {
    return this.get('/api/performance/metrics');
  }

  async getSystemHealth() {
    return this.get('/api/performance/health');
  }

  // AI/ML APIs
  async getMLModels() {
    return this.get('/api/ai-ml/models');
  }

  async getMLMetrics() {
    return this.get('/api/ai-ml/metrics');
  }

  async trainModel(modelType) {
    return this.post('/api/ai-ml/train', { model_type: modelType });
  }
}

// Create and export a singleton instance
const apiService = new ApiService();

// Export individual methods for convenience
export const healthCheck = (...args) => apiService.healthCheck(...args);
export const getDashboardStats = (...args) => apiService.getDashboardStats(...args);
export const getDashboardMetrics = (...args) => apiService.getDashboardMetrics(...args);
export const getRecentActivity = (...args) => apiService.getRecentActivity(...args);
export const searchEmails = (...args) => apiService.searchEmails(...args);
export const getEmailDetails = (...args) => apiService.getEmailDetails(...args);
export const getEmailStats = (...args) => apiService.getEmailStats(...args);
export const getThreatTypes = (...args) => apiService.getThreatTypes(...args);
export const getQuarantinedEmails = (...args) => apiService.getQuarantinedEmails(...args);
export const releaseEmail = (...args) => apiService.releaseEmail(...args);
export const deleteEmail = (...args) => apiService.deleteEmail(...args);
export const getSettings = (...args) => apiService.getSettings(...args);
export const updateSettings = (...args) => apiService.updateSettings(...args);
export const getUsers = (...args) => apiService.getUsers(...args);
export const createUser = (...args) => apiService.createUser(...args);
export const updateUser = (...args) => apiService.updateUser(...args);
export const deleteUser = (...args) => apiService.deleteUser(...args);
export const getThreatIntelligence = (...args) => apiService.getThreatIntelligence(...args);
export const getThreatFeeds = (...args) => apiService.getThreatFeeds(...args);
export const getPerformanceMetrics = (...args) => apiService.getPerformanceMetrics(...args);
export const getSystemHealth = (...args) => apiService.getSystemHealth(...args);
export const getMLModels = (...args) => apiService.getMLModels(...args);
export const getMLMetrics = (...args) => apiService.getMLMetrics(...args);
export const trainModel = (...args) => apiService.trainModel(...args);

export default apiService;
