import React, { useState } from 'react';
import { User, LogIn, UserPlus } from 'lucide-react';

const UserAuth = ({ onUserChange, currentUser }) => {
  const [showAuth, setShowAuth] = useState(false);
  const [userId, setUserId] = useState('');

  const handleLogin = () => {
    if (userId.trim()) {
      onUserChange(userId.trim());
      setShowAuth(false);
      setUserId('');
    }
  };

  const handleDemoUser = (demoId) => {
    onUserChange(demoId);
    setShowAuth(false);
  };

  if (!showAuth) {
    return (
      <div className="bg-white border rounded-lg p-3 mb-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <User className="w-4 h-4 text-blue-600 mr-2" />
            <span className="text-sm text-gray-700">
              Current User: <strong>{currentUser}</strong>
            </span>
          </div>
          <button
            onClick={() => setShowAuth(true)}
            className="px-3 py-1 text-xs bg-blue-100 hover:bg-blue-200 text-blue-700 rounded"
          >
            Switch User
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border rounded-lg p-4 mb-4">
      <h3 className="text-sm font-medium text-gray-900 mb-3 flex items-center">
        <LogIn className="w-4 h-4 mr-2" />
        User Authentication Demo
      </h3>
      
      <div className="space-y-3">
        <div>
          <label className="block text-xs text-gray-600 mb-1">Enter User ID:</label>
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="e.g. user123, john.doe, etc."
            className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={handleLogin}
            disabled={!userId.trim()}
            className="flex-1 px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded disabled:opacity-50 flex items-center justify-center"
          >
            <UserPlus className="w-3 h-3 mr-1" />
            Login/Create
          </button>
          <button
            onClick={() => setShowAuth(false)}
            className="px-3 py-1 text-xs bg-gray-200 hover:bg-gray-300 text-gray-700 rounded"
          >
            Cancel
          </button>
        </div>
        
        <div className="border-t pt-2">
          <p className="text-xs text-gray-500 mb-2">Quick demo users:</p>
          <div className="flex space-x-1">
            {['demo_user', 'creator1', 'agency_user'].map(demo => (
              <button
                key={demo}
                onClick={() => handleDemoUser(demo)}
                className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 rounded"
              >
                {demo}
              </button>
            ))}
          </div>
        </div>
      </div>
      
      <div className="bg-blue-50 p-2 rounded mt-3">
        <p className="text-xs text-blue-700">
          💡 In a real SaaS, this would be handled by your authentication system (Auth0, Firebase, etc.)
        </p>
      </div>
    </div>
  );
};

export default UserAuth;