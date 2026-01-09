import React, { useState, useEffect } from 'react';
import { Save, Eye, EyeOff, Key, Globe, Mic, Youtube, AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || '';

const SettingsNew = ({ userId = 'demo_user' }) => {
  const [activeSection, setActiveSection] = useState('api-keys');
  const [showKeys, setShowKeys] = useState({});
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);
  
  const [apiKeys, setApiKeys] = useState({
    openai_api_key: '',
    elevenlabs_api_key: '',
    serp_api_key: '',
    perplexity_api_key: '',
  });

  const [preferences, setPreferences] = useState({
    trending_region: 'US',
    language: 'english',
    script_tone: 'energetic',
    auto_upload: false,
  });

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/user/${userId}/settings`);
      if (response.ok) {
        const data = await response.json();
        if (data.api_keys) setApiKeys(data.api_keys);
        if (data.preferences) setPreferences(data.preferences);
      }
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    }
  };

  const saveSettings = async () => {
    try {
      setError(null);
      const response = await fetch(`${API_BASE}/api/user/${userId}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_keys: apiKeys, preferences }),
      });

      if (response.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      } else {
        throw new Error('Failed to save settings');
      }
    } catch (error) {
      setError(error.message);
      console.error('Failed to save settings:', error);
    }
  };

  const toggleKeyVisibility = (keyName) => {
    setShowKeys(prev => ({ ...prev, [keyName]: !prev[keyName] }));
  };

  const maskKey = (key) => {
    if (!key) return '';
    if (key.length <= 8) return '•'.repeat(key.length);
    return key.substring(0, 4) + '•'.repeat(key.length - 8) + key.substring(key.length - 4);
  };

  const sections = [
    { id: 'api-keys', name: 'API Keys', icon: Key },
    { id: 'preferences', name: 'Preferences', icon: Globe },
  ];

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm md:text-base text-gray-600 mt-1">Manage your API keys and preferences</p>
      </div>

      {/* Save Banner */}
      {saved && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-2 animate-fade-in">
          <CheckCircle className="w-5 h-5 text-green-600" />
          <span className="text-sm font-medium text-green-800">Settings saved successfully!</span>
        </div>
      )}

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center space-x-2">
          <AlertCircle className="w-5 h-5 text-red-600" />
          <span className="text-sm font-medium text-red-800">{error}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar Navigation */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-xl border border-gray-200 p-2 shadow-sm">
            {sections.map((section) => (
              <button
                key={section.id}
                onClick={() => setActiveSection(section.id)}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                  activeSection === section.id
                    ? 'bg-blue-50 text-blue-700 font-medium'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
              >
                <section.icon className="w-5 h-5" />
                <span className="text-sm">{section.name}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Content Area */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
            {/* API Keys Section */}
            {activeSection === 'api-keys' && (
              <div className="p-6 space-y-6">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 mb-1">API Keys</h2>
                  <p className="text-sm text-gray-600">Securely store your API keys for various services</p>
                </div>

                <div className="space-y-4">
                  {/* OpenAI API Key */}
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">
                      OpenAI API Key
                      <span className="text-red-500 ml-1">*</span>
                    </label>
                    <div className="relative">
                      <input
                        type={showKeys.openai_api_key ? 'text' : 'password'}
                        value={apiKeys.openai_api_key}
                        onChange={(e) => setApiKeys({...apiKeys, openai_api_key: e.target.value})}
                        placeholder="sk-..."
                        className="w-full px-4 py-2.5 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      />
                      <button
                        type="button"
                        onClick={() => toggleKeyVisibility('openai_api_key')}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showKeys.openai_api_key ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                      </button>
                    </div>
                    <p className="text-xs text-gray-500">Required for script generation. Get your key from <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">OpenAI</a></p>
                  </div>

                  {/* ElevenLabs API Key */}
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">
                      ElevenLabs API Key
                      <span className="text-red-500 ml-1">*</span>
                    </label>
                    <div className="relative">
                      <input
                        type={showKeys.elevenlabs_api_key ? 'text' : 'password'}
                        value={apiKeys.elevenlabs_api_key}
                        onChange={(e) => setApiKeys({...apiKeys, elevenlabs_api_key: e.target.value})}
                        placeholder="Enter your ElevenLabs API key"
                        className="w-full px-4 py-2.5 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      />
                      <button
                        type="button"
                        onClick={() => toggleKeyVisibility('elevenlabs_api_key')}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showKeys.elevenlabs_api_key ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                      </button>
                    </div>
                    <p className="text-xs text-gray-500">Required for voice generation. Get your key from <a href="https://elevenlabs.io" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">ElevenLabs</a></p>
                  </div>

                  {/* SERP API Key */}
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">
                      SerpAPI Key
                      <span className="text-red-500 ml-1">*</span>
                    </label>
                    <div className="relative">
                      <input
                        type={showKeys.serp_api_key ? 'text' : 'password'}
                        value={apiKeys.serp_api_key}
                        onChange={(e) => setApiKeys({...apiKeys, serp_api_key: e.target.value})}
                        placeholder="Enter your SerpAPI key"
                        className="w-full px-4 py-2.5 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      />
                      <button
                        type="button"
                        onClick={() => toggleKeyVisibility('serp_api_key')}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showKeys.serp_api_key ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                      </button>
                    </div>
                    <p className="text-xs text-gray-500">Required for trending topics. Get your key from <a href="https://serpapi.com" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">SerpAPI</a></p>
                  </div>

                  {/* Perplexity API Key */}
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">
                      Perplexity API Key
                      <span className="text-gray-400 ml-1 text-xs">(Optional)</span>
                    </label>
                    <div className="relative">
                      <input
                        type={showKeys.perplexity_api_key ? 'text' : 'password'}
                        value={apiKeys.perplexity_api_key}
                        onChange={(e) => setApiKeys({...apiKeys, perplexity_api_key: e.target.value})}
                        placeholder="Enter your Perplexity API key (optional)"
                        className="w-full px-4 py-2.5 pr-12 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                      />
                      <button
                        type="button"
                        onClick={() => toggleKeyVisibility('perplexity_api_key')}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                      >
                        {showKeys.perplexity_api_key ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                      </button>
                    </div>
                    <p className="text-xs text-gray-500">Optional for enhanced research. Get your key from <a href="https://www.perplexity.ai" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Perplexity</a></p>
                  </div>
                </div>
              </div>
            )}

            {/* Preferences Section */}
            {activeSection === 'preferences' && (
              <div className="p-6 space-y-6">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 mb-1">Preferences</h2>
                  <p className="text-sm text-gray-600">Customize your default automation settings</p>
                </div>

                <div className="space-y-4">
                  {/* Trending Region */}
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">Default Trending Region</label>
                    <select
                      value={preferences.trending_region}
                      onChange={(e) => setPreferences({...preferences, trending_region: e.target.value})}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    >
                      <option value="US">United States</option>
                      <option value="AU">Australia</option>
                      <option value="GB">United Kingdom</option>
                      <option value="CA">Canada</option>
                      <option value="IN">India</option>
                      <option value="JP">Japan</option>
                      <option value="DE">Germany</option>
                      <option value="FR">France</option>
                      <option value="BR">Brazil</option>
                    </select>
                  </div>

                  {/* Language */}
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">Default Language</label>
                    <select
                      value={preferences.language}
                      onChange={(e) => setPreferences({...preferences, language: e.target.value})}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    >
                      <option value="english">English</option>
                      <option value="hinglish">Hinglish</option>
                    </select>
                  </div>

                  {/* Script Tone */}
                  <div className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">Default Script Tone</label>
                    <select
                      value={preferences.script_tone}
                      onChange={(e) => setPreferences({...preferences, script_tone: e.target.value})}
                      className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                    >
                      <option value="energetic">Energetic</option>
                      <option value="professional">Professional</option>
                      <option value="casual">Casual</option>
                      <option value="dramatic">Dramatic</option>
                    </select>
                  </div>

                  {/* Auto Upload */}
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div>
                      <label className="block text-sm font-medium text-gray-700">Auto-Upload to YouTube</label>
                      <p className="text-xs text-gray-500 mt-1">Automatically upload videos after generation</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={preferences.auto_upload}
                        onChange={(e) => setPreferences({...preferences, auto_upload: e.target.checked})}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                </div>
              </div>
            )}

            {/* Save Button */}
            <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 rounded-b-xl">
              <button
                onClick={saveSettings}
                className="w-full md:w-auto flex items-center justify-center px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all duration-200 font-medium shadow-sm hover:shadow-md"
              >
                <Save className="w-4 h-4 mr-2" />
                Save Changes
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SettingsNew;
