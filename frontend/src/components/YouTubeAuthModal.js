import React, { useState } from 'react';
import { X, Youtube, Key, Copy, CheckCircle, ExternalLink, AlertCircle } from 'lucide-react';

const YouTubeAuthModal = ({ isOpen, onClose, onSuccess, userId = 'demo_user' }) => {
  const [authStep, setAuthStep] = useState(1);
  const [authUrl, setAuthUrl] = useState('');
  const [authCode, setAuthCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const startAuth = async () => {
    try {
      setLoading(true);
      setError('');
      
      const response = await fetch(`/youtube/auth/start?user_id=${userId}`);
      if (response.ok) {
        const data = await response.json();
        setAuthUrl(data.auth_url);
        setAuthStep(2);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to start authentication');
      }
    } catch (error) {
      setError('Failed to connect to server');
    } finally {
      setLoading(false);
    }
  };

  const completeAuth = async () => {
    if (!authCode.trim()) {
      setError('Please enter the authorization code');
      return;
    }

    try {
      setLoading(true);
      setError('');

      const response = await fetch('/youtube/auth/callback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          auth_code: authCode.trim(),
          user_id: userId 
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setAuthStep(3);
        setTimeout(() => {
          onSuccess(data.channel_info);
          resetModal();
        }, 2000);
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Authentication failed');
      }
    } catch (error) {
      setError('Failed to complete authentication');
    } finally {
      setLoading(false);
    }
  };

  const resetModal = () => {
    setAuthStep(1);
    setAuthUrl('');
    setAuthCode('');
    setError('');
    setLoading(false);
    onClose();
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(authUrl);
    } catch (error) {
      console.error('Failed to copy to clipboard');
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <div className="flex items-center">
            <Youtube className="w-5 h-5 text-red-600 mr-2" />
            <h3 className="text-lg font-semibold">Add YouTube Channel</h3>
          </div>
          <button onClick={resetModal} className="text-gray-400 hover:text-gray-600">
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
            <div className="flex items-center">
              <AlertCircle className="w-4 h-4 text-red-600 mr-2" />
              <span className="text-red-700 text-sm">{error}</span>
            </div>
          </div>
        )}

        {authStep === 1 && (
          <div>
            <p className="text-gray-600 mb-4">
              To add a new YouTube channel, you'll need to authenticate with Google to grant access to your YouTube account.
            </p>
            <div className="bg-blue-50 p-3 rounded-lg mb-4">
              <h4 className="font-medium text-blue-900 mb-2">What you'll need:</h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• Access to the Google account that owns the YouTube channel</li>
                <li>• Permission to manage YouTube channels on that account</li>
                <li>• A few minutes to complete the authorization process</li>
              </ul>
            </div>
            <button
              onClick={startAuth}
              disabled={loading}
              className="w-full bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg disabled:opacity-50 flex items-center justify-center"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Starting...
                </>
              ) : (
                <>
                  <Key className="w-4 h-4 mr-2" />
                  Start Authentication
                </>
              )}
            </button>
          </div>
        )}

        {authStep === 2 && (
          <div>
            <p className="text-gray-600 mb-4">
              Follow these steps to complete the authentication:
            </p>
            <div className="space-y-3 mb-4">
              <div className="flex items-start">
                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full mr-3 mt-0.5">1</span>
                <div>
                  <p className="text-sm">Click the link below to open Google authentication:</p>
                  <div className="bg-gray-50 p-2 rounded border mt-2 break-all text-xs">
                    <a href={authUrl} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-blue-800">
                      {authUrl}
                    </a>
                  </div>
                  <div className="flex space-x-2 mt-2">
                    <button
                      onClick={copyToClipboard}
                      className="text-xs bg-gray-200 hover:bg-gray-300 px-2 py-1 rounded flex items-center"
                    >
                      <Copy className="w-3 h-3 mr-1" />
                      Copy
                    </button>
                    <a
                      href={authUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1 rounded flex items-center"
                    >
                      <ExternalLink className="w-3 h-3 mr-1" />
                      Open
                    </a>
                  </div>
                </div>
              </div>
              
              <div className="flex items-start">
                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full mr-3 mt-0.5">2</span>
                <p className="text-sm">Sign in with your Google account and grant permissions</p>
              </div>
              
              <div className="flex items-start">
                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full mr-3 mt-0.5">3</span>
                <p className="text-sm">Copy the authorization code and paste it below</p>
              </div>
            </div>

            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Authorization Code:
              </label>
              <input
                type="text"
                value={authCode}
                onChange={(e) => setAuthCode(e.target.value)}
                placeholder="Paste the authorization code here..."
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="flex space-x-3">
              <button
                onClick={resetModal}
                className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-700 px-4 py-2 rounded-lg"
              >
                Cancel
              </button>
              <button
                onClick={completeAuth}
                disabled={loading || !authCode.trim()}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg disabled:opacity-50 flex items-center justify-center"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Verifying...
                  </>
                ) : (
                  'Complete Setup'
                )}
              </button>
            </div>
          </div>
        )}

        {authStep === 3 && (
          <div className="text-center">
            <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-4" />
            <h4 className="text-lg font-semibold text-green-900 mb-2">Success!</h4>
            <p className="text-green-700 mb-4">
              Your YouTube channel has been authenticated and added to the system.
            </p>
            <div className="bg-green-50 p-3 rounded-lg">
              <p className="text-sm text-green-700">
                The channel list will be refreshed automatically.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default YouTubeAuthModal;