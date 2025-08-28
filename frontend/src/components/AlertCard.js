import React from 'react';
import { ExclamationTriangleIcon, InformationCircleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';

function AlertCard({ alert }) {
  const getIcon = () => {
    switch (alert.severity) {
      case 'high':
        return ExclamationTriangleIcon;
      case 'medium':
        return InformationCircleIcon;
      case 'low':
        return CheckCircleIcon;
      default:
        return InformationCircleIcon;
    }
  };

  const getSeverityColor = () => {
    switch (alert.severity) {
      case 'high':
        return 'border-privik-red-200 bg-privik-red-50';
      case 'medium':
        return 'border-yellow-200 bg-yellow-50';
      case 'low':
        return 'border-privik-green-200 bg-privik-green-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  const getSeverityTextColor = () => {
    switch (alert.severity) {
      case 'high':
        return 'text-privik-red-800';
      case 'medium':
        return 'text-yellow-800';
      case 'low':
        return 'text-privik-green-800';
      default:
        return 'text-gray-800';
    }
  };

  const Icon = getIcon();

  return (
    <div className={`border rounded-lg p-4 ${getSeverityColor()}`}>
      <div className="flex items-start">
        <Icon className={`h-5 w-5 mt-0.5 mr-3 ${getSeverityTextColor()}`} />
        <div className="flex-1">
          <h4 className={`text-sm font-medium ${getSeverityTextColor()}`}>
            {alert.title}
          </h4>
          <p className="text-sm text-gray-600 mt-1">
            {alert.description}
          </p>
          <div className="flex items-center justify-between mt-3">
            <span className="text-xs text-gray-500">
              {new Date(alert.timestamp).toLocaleString()}
            </span>
            <span className={`status-badge status-${alert.severity}`}>
              {alert.severity.toUpperCase()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AlertCard;
