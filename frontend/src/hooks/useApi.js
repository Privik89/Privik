import { useState, useEffect, useCallback } from 'react';
import apiService from '../services/api';

// Custom hook for API calls with loading states and error handling
export const useApi = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(async (apiCall, ...args) => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiCall(...args);
      return result;
    } catch (err) {
      setError(err.message || 'An error occurred');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { execute, loading, error };
};

// Hook for dashboard data
export const useDashboardData = (timeRange = '24h') => {
  const [data, setData] = useState(null);
  const { execute, loading, error } = useApi();

  const fetchData = useCallback(async () => {
    try {
      const stats = await execute(apiService.getDashboardStats, timeRange);
      const metrics = await execute(apiService.getDashboardMetrics);
      const activity = await execute(apiService.getRecentActivity, 10);
      
      setData({
        stats,
        metrics,
        activity
      });
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    }
  }, [execute, timeRange]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const refresh = useCallback(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refresh };
};

// Hook for email search
export const useEmailSearch = () => {
  const [results, setResults] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const { execute, loading, error } = useApi();

  const search = useCallback(async (query, filters = {}) => {
    try {
      const response = await execute(apiService.searchEmails, query, filters);
      setResults(response.results || []);
      setTotalCount(response.total || 0);
      return response;
    } catch (err) {
      setResults([]);
      setTotalCount(0);
      throw err;
    }
  }, [execute]);

  const clearResults = useCallback(() => {
    setResults([]);
    setTotalCount(0);
  }, []);

  return { results, totalCount, search, clearResults, loading, error };
};

// Hook for settings
export const useSettings = () => {
  const [settings, setSettings] = useState(null);
  const { execute, loading, error } = useApi();

  const fetchSettings = useCallback(async () => {
    try {
      const data = await execute(apiService.getSettings);
      setSettings(data);
      return data;
    } catch (err) {
      console.error('Failed to fetch settings:', err);
      throw err;
    }
  }, [execute]);

  const updateSettings = useCallback(async (newSettings) => {
    try {
      const data = await execute(apiService.updateSettings, newSettings);
      setSettings(data);
      return data;
    } catch (err) {
      console.error('Failed to update settings:', err);
      throw err;
    }
  }, [execute]);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  return { settings, updateSettings, loading, error, refresh: fetchSettings };
};

// Hook for users
export const useUsers = () => {
  const [users, setUsers] = useState([]);
  const { execute, loading, error } = useApi();

  const fetchUsers = useCallback(async () => {
    try {
      const data = await execute(apiService.getUsers);
      setUsers(data);
      return data;
    } catch (err) {
      console.error('Failed to fetch users:', err);
      throw err;
    }
  }, [execute]);

  const createUser = useCallback(async (userData) => {
    try {
      const newUser = await execute(apiService.createUser, userData);
      setUsers(prev => [...prev, newUser]);
      return newUser;
    } catch (err) {
      console.error('Failed to create user:', err);
      throw err;
    }
  }, [execute]);

  const updateUser = useCallback(async (userId, userData) => {
    try {
      const updatedUser = await execute(apiService.updateUser, userId, userData);
      setUsers(prev => prev.map(user => user.id === userId ? updatedUser : user));
      return updatedUser;
    } catch (err) {
      console.error('Failed to update user:', err);
      throw err;
    }
  }, [execute]);

  const deleteUser = useCallback(async (userId) => {
    try {
      await execute(apiService.deleteUser, userId);
      setUsers(prev => prev.filter(user => user.id !== userId));
    } catch (err) {
      console.error('Failed to delete user:', err);
      throw err;
    }
  }, [execute]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  return { 
    users, 
    createUser, 
    updateUser, 
    deleteUser, 
    loading, 
    error, 
    refresh: fetchUsers 
  };
};

// Hook for threat intelligence
export const useThreatIntelligence = () => {
  const [threatData, setThreatData] = useState(null);
  const { execute, loading, error } = useApi();

  const fetchThreatData = useCallback(async () => {
    try {
      const data = await execute(apiService.getThreatIntelligence);
      setThreatData(data);
      return data;
    } catch (err) {
      console.error('Failed to fetch threat intelligence:', err);
      throw err;
    }
  }, [execute]);

  useEffect(() => {
    fetchThreatData();
  }, [fetchThreatData]);

  return { threatData, loading, error, refresh: fetchThreatData };
};

// Hook for performance metrics
export const usePerformanceMetrics = () => {
  const [metrics, setMetrics] = useState(null);
  const { execute, loading, error } = useApi();

  const fetchMetrics = useCallback(async () => {
    try {
      const data = await execute(apiService.getPerformanceMetrics);
      setMetrics(data);
      return data;
    } catch (err) {
      console.error('Failed to fetch performance metrics:', err);
      throw err;
    }
  }, [execute]);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  return { metrics, loading, error, refresh: fetchMetrics };
};
