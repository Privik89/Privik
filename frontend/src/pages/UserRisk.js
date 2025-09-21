import React from 'react';

function UserRisk() {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-900">User Risk Assessment</h1>
        <p className="text-gray-600 mt-2">Monitor user behavior and risk levels</p>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Risk Levels</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
            <h3 className="font-medium text-red-900">High Risk Users</h3>
            <p className="text-2xl font-bold text-red-600 mt-2">3</p>
            <p className="text-sm text-red-700">Users requiring immediate attention</p>
          </div>
          <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <h3 className="font-medium text-yellow-900">Medium Risk Users</h3>
            <p className="text-2xl font-bold text-yellow-600 mt-2">12</p>
            <p className="text-sm text-yellow-700">Users with elevated risk factors</p>
          </div>
          <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
            <h3 className="font-medium text-green-900">Low Risk Users</h3>
            <p className="text-2xl font-bold text-green-600 mt-2">141</p>
            <p className="text-sm text-green-700">Users with normal risk levels</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default UserRisk;