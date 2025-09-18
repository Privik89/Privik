import React, { useState, useEffect } from 'react';

const AIMLDashboard = () => {
  const [aiStatus, setAiStatus] = useState(null);
  const [behavioralInsights, setBehavioralInsights] = useState(null);
  const [threatHuntingCampaigns, setThreatHuntingCampaigns] = useState([]);
  const [huntingRules, setHuntingRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        fetchAIStatus(),
        fetchBehavioralInsights(),
        fetchThreatHuntingCampaigns(),
        fetchHuntingRules()
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchAIStatus = async () => {
    try {
      const response = await fetch('/api/ui/ai-ml/ai/status');
      if (!response.ok) throw new Error('Failed to fetch AI status');
      const data = await response.json();
      setAiStatus(data);
    } catch (err) {
      console.error('Failed to fetch AI status:', err);
    }
  };

  const fetchBehavioralInsights = async () => {
    try {
      const response = await fetch('/api/ui/ai-ml/behavior/insights');
      if (!response.ok) throw new Error('Failed to fetch behavioral insights');
      const data = await response.json();
      setBehavioralInsights(data);
    } catch (err) {
      console.error('Failed to fetch behavioral insights:', err);
    }
  };

  const fetchThreatHuntingCampaigns = async () => {
    try {
      const response = await fetch('/api/ui/ai-ml/threat-hunting/campaigns?limit=5');
      if (!response.ok) throw new Error('Failed to fetch threat hunting campaigns');
      const data = await response.json();
      setThreatHuntingCampaigns(data.campaigns || []);
    } catch (err) {
      console.error('Failed to fetch threat hunting campaigns:', err);
    }
  };

  const fetchHuntingRules = async () => {
    try {
      const response = await fetch('/api/ui/ai-ml/threat-hunting/rules');
      if (!response.ok) throw new Error('Failed to fetch hunting rules');
      const data = await response.json();
      setHuntingRules(data.rules || []);
    } catch (err) {
      console.error('Failed to fetch hunting rules:', err);
    }
  };

  const handleTrainModels = async () => {
    try {
      const response = await fetch('/api/ui/ai-ml/ml/train?days_back=30', {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to start ML training');
      const result = await response.json();
      alert(result.message);
      fetchAIStatus();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleRunThreatHunting = async () => {
    try {
      const campaignName = prompt('Enter campaign name:');
      if (!campaignName) return;

      const response = await fetch(`/api/ui/ai-ml/threat-hunting/campaign?campaign_name=${encodeURIComponent(campaignName)}&time_range=7`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('Failed to start threat hunting campaign');
      const result = await response.json();
      alert(result.message);
      fetchThreatHuntingCampaigns();
    } catch (err) {
      setError(err.message);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'operational':
        return 'text-green-600 bg-green-100';
      case 'degraded':
        return 'text-yellow-600 bg-yellow-100';
      case 'error':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 bg-red-100';
      case 'high':
        return 'text-orange-600 bg-orange-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'low':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  if (loading && !aiStatus) {
    return <div className="p-4">Loading AI/ML dashboard...</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">AI/ML Dashboard</h3>
        <div className="flex gap-2">
          <button
            onClick={handleTrainModels}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Train Models
          </button>
          <button
            onClick={handleRunThreatHunting}
            className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
          >
            Run Threat Hunting
          </button>
          <button
            onClick={fetchAllData}
            className="px-4 py-2 bg-privik-blue-600 text-white rounded hover:bg-privik-blue-700"
          >
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      {/* Overall Status */}
      {aiStatus && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-4">
            <span className={`px-3 py-1 rounded-full font-medium ${getStatusColor(aiStatus.overall_status)}`}>
              {aiStatus.overall_status.toUpperCase()}
            </span>
            <span className="text-sm text-gray-600">
              Last Updated: {new Date(aiStatus.timestamp).toLocaleString()}
            </span>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {['overview', 'ml-models', 'behavioral', 'threat-hunting', 'sandbox'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-2 px-1 border-b-2 font-medium text-sm capitalize ${
                  activeTab === tab
                    ? 'border-privik-blue-500 text-privik-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.replace('-', ' ')}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* ML Models Status */}
          {aiStatus && aiStatus.ml_models && (
            <div>
              <h4 className="font-medium text-gray-900 mb-3">ML Models Status</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {Object.entries(aiStatus.ml_models.status).map(([modelName, status]) => (
                  <div key={modelName} className="p-4 border rounded-lg">
                    <div className="flex justify-between items-center mb-2">
                      <h5 className="font-medium text-gray-900 capitalize">{modelName.replace('_', ' ')}</h5>
                      <span className={`px-2 py-1 text-xs rounded-full ${status.loaded ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
                        {status.loaded ? 'Loaded' : 'Not Loaded'}
                      </span>
                    </div>
                    {status.type && (
                      <div className="text-sm text-gray-600">
                        Type: {status.type}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Behavioral Analysis */}
          {behavioralInsights && (
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Behavioral Analysis</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="p-4 border rounded-lg text-center">
                  <div className="text-2xl font-bold text-gray-900">{behavioralInsights.total_users || 0}</div>
                  <div className="text-sm text-gray-600">Total Users</div>
                </div>
                <div className="p-4 border rounded-lg text-center">
                  <div className="text-2xl font-bold text-red-600">{behavioralInsights.high_risk_users || 0}</div>
                  <div className="text-sm text-gray-600">High Risk</div>
                </div>
                <div className="p-4 border rounded-lg text-center">
                  <div className="text-2xl font-bold text-orange-600">{behavioralInsights.medium_risk_users || 0}</div>
                  <div className="text-sm text-gray-600">Medium Risk</div>
                </div>
                <div className="p-4 border rounded-lg text-center">
                  <div className="text-2xl font-bold text-green-600">{behavioralInsights.low_risk_users || 0}</div>
                  <div className="text-sm text-gray-600">Low Risk</div>
                </div>
              </div>
            </div>
          )}

          {/* Threat Hunting */}
          {aiStatus && aiStatus.threat_hunting && (
            <div>
              <h4 className="font-medium text-gray-900 mb-3">Threat Hunting</h4>
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 border rounded-lg">
                  <h5 className="font-medium text-gray-900 mb-2">Available Rules</h5>
                  <div className="text-2xl font-bold text-gray-900">{aiStatus.threat_hunting.rules_available}</div>
                </div>
                <div className="p-4 border rounded-lg">
                  <h5 className="font-medium text-gray-900 mb-2">Active Campaigns</h5>
                  <div className="text-2xl font-bold text-gray-900">{aiStatus.threat_hunting.active_campaigns}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ML Models Tab */}
      {activeTab === 'ml-models' && aiStatus && (
        <div className="space-y-6">
          <div className="p-4 border rounded-lg">
            <h4 className="font-medium text-gray-900 mb-3">Machine Learning Models</h4>
            <div className="space-y-4">
              {Object.entries(aiStatus.ml_models.status).map(([modelName, status]) => (
                <div key={modelName} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div>
                    <h5 className="font-medium text-gray-900 capitalize">{modelName.replace('_', ' ')}</h5>
                    <p className="text-sm text-gray-600">
                      {status.type || 'Unknown type'} • {status.loaded ? 'Ready for inference' : 'Not loaded'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-3 py-1 text-sm rounded-full ${status.loaded ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
                      {status.loaded ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Behavioral Tab */}
      {activeTab === 'behavioral' && behavioralInsights && (
        <div className="space-y-6">
          <div className="p-4 border rounded-lg">
            <h4 className="font-medium text-gray-900 mb-3">User Risk Distribution</h4>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">High Risk Users</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-red-600 h-2 rounded-full" 
                      style={{ width: `${((behavioralInsights.high_risk_users || 0) / Math.max(behavioralInsights.total_users || 1, 1)) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium">{behavioralInsights.high_risk_users || 0}</span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Medium Risk Users</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-orange-600 h-2 rounded-full" 
                      style={{ width: `${((behavioralInsights.medium_risk_users || 0) / Math.max(behavioralInsights.total_users || 1, 1)) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium">{behavioralInsights.medium_risk_users || 0}</span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-600">Low Risk Users</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full" 
                      style={{ width: `${((behavioralInsights.low_risk_users || 0) / Math.max(behavioralInsights.total_users || 1, 1)) * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium">{behavioralInsights.low_risk_users || 0}</span>
                </div>
              </div>
            </div>
          </div>

          {behavioralInsights.top_risk_factors && behavioralInsights.top_risk_factors.length > 0 && (
            <div className="p-4 border rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3">Top Risk Factors</h4>
              <div className="space-y-2">
                {behavioralInsights.top_risk_factors.map(([factor, count], index) => (
                  <div key={factor} className="flex justify-between items-center">
                    <span className="text-sm text-gray-600 capitalize">{factor.replace('_', ' ')}</span>
                    <span className="text-sm font-medium">{count} users</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Threat Hunting Tab */}
      {activeTab === 'threat-hunting' && (
        <div className="space-y-6">
          {/* Hunting Rules */}
          <div className="p-4 border rounded-lg">
            <h4 className="font-medium text-gray-900 mb-3">Threat Hunting Rules</h4>
            <div className="space-y-3">
              {huntingRules.map((rule) => (
                <div key={rule.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div>
                    <h5 className="font-medium text-gray-900">{rule.name}</h5>
                    <p className="text-sm text-gray-600">{rule.description}</p>
                    <div className="flex gap-2 mt-1">
                      <span className="text-xs text-gray-500 capitalize">{rule.category.replace('_', ' ')}</span>
                      <span className={`px-2 py-1 text-xs rounded-full ${getSeverityColor(rule.severity)}`}>
                        {rule.severity}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${rule.enabled ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}`}>
                      {rule.enabled ? 'Enabled' : 'Disabled'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Campaigns */}
          <div className="p-4 border rounded-lg">
            <h4 className="font-medium text-gray-900 mb-3">Recent Campaigns</h4>
            <div className="space-y-3">
              {threatHuntingCampaigns.map((campaign) => (
                <div key={campaign.campaign_id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                  <div>
                    <h5 className="font-medium text-gray-900">{campaign.campaign_name}</h5>
                    <p className="text-sm text-gray-600">
                      Started: {new Date(campaign.start_time).toLocaleString()}
                      {campaign.findings_count > 0 && ` • ${campaign.findings_count} findings`}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${campaign.status === 'completed' ? 'bg-green-100 text-green-600' : 'bg-blue-100 text-blue-600'}`}>
                      {campaign.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Advanced Sandbox Tab */}
      {activeTab === 'sandbox' && aiStatus && aiStatus.advanced_sandbox && (
        <div className="space-y-6">
          <div className="p-4 border rounded-lg">
            <h4 className="font-medium text-gray-900 mb-3">Advanced Sandbox Capabilities</h4>
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-gray-50 rounded">
                <h5 className="font-medium text-gray-900 mb-2">Available Environments</h5>
                <div className="text-2xl font-bold text-gray-900">{aiStatus.advanced_sandbox.environments_available}</div>
                <div className="text-sm text-gray-600">Windows, macOS, Linux</div>
              </div>
              <div className="p-4 bg-gray-50 rounded">
                <h5 className="font-medium text-gray-900 mb-2">Evasion Detectors</h5>
                <div className="text-2xl font-bold text-gray-900">{aiStatus.advanced_sandbox.evasion_detectors}</div>
                <div className="text-sm text-gray-600">Timing, Behavior, Environment, Network</div>
              </div>
            </div>
          </div>

          <div className="p-4 border rounded-lg">
            <h4 className="font-medium text-gray-900 mb-3">Evasion Detection Capabilities</h4>
            <div className="space-y-2">
              {['Timing Analysis', 'Behavior Analysis', 'Environment Analysis', 'Network Analysis'].map((detector) => (
                <div key={detector} className="flex items-center gap-2">
                  <span className="w-2 h-2 bg-green-500 rounded-full"></span>
                  <span className="text-sm text-gray-700">{detector}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIMLDashboard;
