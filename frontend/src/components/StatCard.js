import React from 'react';

function StatCard({ title, value, change, changeType = 'neutral', icon: Icon }) {
  const getChangeColor = () => {
    switch (changeType) {
      case 'positive':
        return 'text-privik-green-600';
      case 'negative':
        return 'text-privik-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getChangeIcon = () => {
    switch (changeType) {
      case 'positive':
        return '↗';
      case 'negative':
        return '↘';
      default:
        return '→';
    }
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {change && (
            <p className={`text-sm font-medium ${getChangeColor()}`}>
              {getChangeIcon()} {change}
            </p>
          )}
        </div>
        {Icon && (
          <div className="p-3 bg-privik-blue-50 rounded-lg">
            <Icon className="h-6 w-6 text-privik-blue-600" />
          </div>
        )}
      </div>
    </div>
  );
}

export default StatCard;
