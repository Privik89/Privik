import React from 'react';

function EmailAnalysis() {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h1 className="text-2xl font-bold text-gray-900">Email Analysis</h1>
        <p className="text-gray-600 mt-2">Analyze and monitor email traffic</p>
      </div>
      
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Email Analysis Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-4 border border-gray-200 rounded-lg">
            <h3 className="font-medium text-gray-900">Real-time Scanning</h3>
            <p className="text-sm text-gray-600 mt-2">Monitor emails as they arrive</p>
          </div>
          <div className="p-4 border border-gray-200 rounded-lg">
            <h3 className="font-medium text-gray-900">Threat Detection</h3>
            <p className="text-sm text-gray-600 mt-2">AI-powered threat identification</p>
          </div>
          <div className="p-4 border border-gray-200 rounded-lg">
            <h3 className="font-medium text-gray-900">Content Analysis</h3>
            <p className="text-sm text-gray-600 mt-2">Deep content inspection</p>
          </div>
          <div className="p-4 border border-gray-200 rounded-lg">
            <h3 className="font-medium text-gray-900">Attachment Scanning</h3>
            <p className="text-sm text-gray-600 mt-2">Safe attachment analysis</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EmailAnalysis;