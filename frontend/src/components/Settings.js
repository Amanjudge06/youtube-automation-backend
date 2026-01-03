import React, { useState, useEffect, useCallback } from 'react';
import { Save, RotateCcw, Key, Globe, Mic, Video, Youtube, Loader2, Plus } from 'lucide-react';
import YouTubeAuthModal from './YouTubeAuthModal';
import UserAuth from './UserAuth';

const Settings = () => {
  const [config, setConfig] = useState({
    // API Keys
    openai_api_key: '',
    elevenlabs_api_key: '',
    serp_api_key: '',
    perplexity_api_key: '',
    youtube_client_id: '',
    youtube_client_secret: '',
    
    // Trending Config
    trending_region: 'AU',
    trending_language: 'en',
    max_topics: 10,
    
    // Script Config
    script_model: 'gpt-4-turbo-preview',
    script_temperature: 0.7,
    script_tone: 'energetic',
    script_language: 'english',
    
    // Video Config
    video_resolution: '1080x1920',
    video_fps: 30,
    video_duration: 60,
    
    // Voice Config
    voice_id: 'default',
    voice_name: 'Default Voice',
    voice_stability: 0.5,
    voice_similarity: 0.75,
    voice_style: 0.2,
    
    // Upload Config
    auto_upload: false,
    video_privacy: 'public',
    auto_thumbnail: true,
    default_channel: ''
  });

  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);
  const [availableVoices, setAvailableVoices] = useState([]);
  const [loadingVoices, setLoadingVoices] = useState(false);
  const [youtubeChannels, setYoutubeChannels] = useState([]);
  const [loadingChannels, setLoadingChannels] = useState(false);
  const [authSuccess, setAuthSuccess] = useState(false);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [userId, setUserId] = useState('demo_user');

  const fetchConfig = useCallback(async () => {
    try {
      const response = await fetch('/api/config');
      const data = await response.json();
      setConfig(prevConfig => ({
        ...prevConfig,
        ...data.trending_config,
        ...data.script_config,
        ...data.video_config,
        ...data.voice_config,
        ...data.upload_config
      }));
    } catch (error) {
      console.error('Failed to fetch config:', error);
    }
  }, []);

  const fetchAvailableVoices = useCallback(async () => {
    try {
      setLoadingVoices(true);
      const response = await fetch('/voices/available');
      if (response.ok) {
        const data = await response.json();
        setAvailableVoices(data.voices);
        
        // Set current voice if available
        const currentResponse = await fetch('/voices/current');
        if (currentResponse.ok) {
          const currentData = await currentResponse.json();
          setConfig(prev => ({
            ...prev,
            voice_id: currentData.voice_id,
            voice_stability: currentData.voice_settings?.stability || 0.5,
            voice_similarity: currentData.voice_settings?.similarity_boost || 0.75,
            voice_style: currentData.voice_settings?.style || 0.2
          }));
        }
      }
    } catch (error) {
      console.error('Failed to fetch voices:', error);
    } finally {
      setLoadingVoices(false);
    }
  }, []);

  const fetchYouTubeChannels = useCallback(async () => {
    try {
      setLoadingChannels(true);
      const response = await fetch(`/youtube/channels/${userId}`);
      if (response.ok) {
        const data = await response.json();
        setYoutubeChannels(data.channels || []);
      }
    } catch (error) {
      console.error('Failed to fetch YouTube channels:', error);
      // Keep empty array for new users
      setYoutubeChannels([]);
    } finally {
      setLoadingChannels(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchConfig();
    fetchAvailableVoices();
    fetchYouTubeChannels();
  }, [fetchConfig, fetchAvailableVoices, fetchYouTubeChannels]);

  const handleAddNewChannel = () => {
    setShowAuthModal(true);
  };

  const handleAuthSuccess = async (channelInfo) => {
    setAuthSuccess(true);
    setTimeout(() => setAuthSuccess(false), 3000);
    
    // Refresh the channels list
    await fetchYouTubeChannels();
  };

  const handleSetActiveChannel = async (channelId) => {
    try {
      const response = await fetch(`/youtube/channels/${userId}/set-active`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ channel_id: channelId }),
      });

      if (response.ok) {
        // Update local state
        setConfig({...config, default_channel: channelId});
        setYoutubeChannels(channels => 
          channels.map(ch => ({
            ...ch,
            is_default: ch.id === channelId
          }))
        );
        
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      }
    } catch (error) {
      console.error('Failed to set active channel:', error);
    }
  };

  const refreshChannels = async () => {
    try {
      setLoadingChannels(true);
      await fetchYouTubeChannels(); // Just refetch the user's channels
      setAuthSuccess(true);
      setTimeout(() => setAuthSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to refresh channels:', error);
    } finally {
      setLoadingChannels(false);
    }
  };

  const handleVoiceChange = async (voiceId, voiceName) => {
    try {
      const response = await fetch('/voices/set', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          voice_id: voiceId,
          voice_name: voiceName
        }),
      });

      if (response.ok) {
        setConfig(prev => ({
          ...prev,
          voice_id: voiceId,
          voice_name: voiceName
        }));
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      }
    } catch (error) {
      console.error('Failed to change voice:', error);
    }
  };

  const saveConfig = async () => {
    setLoading(true);
    try {
      await fetch('/api/config/update', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config)
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error) {
      console.error('Error saving config:', error);
      alert('Failed to save configuration');
    } finally {
      setLoading(false);
    }
  };

  const resetToDefaults = () => {
    if (window.confirm('Are you sure you want to reset all settings to defaults?')) {
      setConfig({
        // Reset to default values
        trending_region: 'AU',
        trending_language: 'en',
        max_topics: 10,
        script_model: 'gpt-4-turbo-preview',
        script_temperature: 0.7,
        script_tone: 'energetic',
        script_language: 'english',
        video_resolution: '1080x1920',
        video_fps: 30,
        video_duration: 60,
        auto_upload: false,
        video_privacy: 'public',
        auto_thumbnail: true
      });
    }
  };

  const ConfigSection = ({ title, icon: Icon, children }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center">
          <Icon className="w-5 h-5 text-gray-600 mr-2" />
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
      </div>
      <div className="p-6 space-y-4">
        {children}
      </div>
    </div>
  );

  const FormField = ({ label, description, children }) => (
    <div className="space-y-1">
      <label className="block text-sm font-medium text-gray-700">
        {label}
      </label>
      {description && (
        <p className="text-xs text-gray-500">{description}</p>
      )}
      {children}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* User Authentication Demo */}
      <UserAuth 
        currentUser={userId} 
        onUserChange={(newUserId) => setUserId(newUserId)} 
      />
      
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600">Configure your automation parameters</p>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={resetToDefaults}
            className="flex items-center px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            <RotateCcw className="w-4 h-4 mr-2" />
            Reset
          </button>
          <button
            onClick={saveConfig}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            <Save className="w-4 h-4 mr-2" />
            {loading ? 'Saving...' : saved ? 'Saved!' : 'Save'}
          </button>
        </div>
      </div>

      {/* API Keys Section */}
      <ConfigSection title="API Keys" icon={Key}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField 
            label="OpenAI API Key" 
            description="For script generation"
          >
            <input
              type="password"
              value={config.openai_api_key}
              onChange={(e) => setConfig({...config, openai_api_key: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              placeholder="sk-..."
            />
          </FormField>
          
          <FormField 
            label="ElevenLabs API Key" 
            description="For voice synthesis"
          >
            <input
              type="password"
              value={config.elevenlabs_api_key}
              onChange={(e) => setConfig({...config, elevenlabs_api_key: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter API key"
            />
          </FormField>
          
          <FormField 
            label="SERP API Key" 
            description="For trending topics and images"
          >
            <input
              type="password"
              value={config.serp_api_key}
              onChange={(e) => setConfig({...config, serp_api_key: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              placeholder="Enter API key"
            />
          </FormField>
          
          <FormField 
            label="Perplexity API Key" 
            description="For topic research"
          >
            <input
              type="password"
              value={config.perplexity_api_key}
              onChange={(e) => setConfig({...config, perplexity_api_key: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              placeholder="pplx-..."
            />
          </FormField>
        </div>
      </ConfigSection>

      {/* Trending Topics Section */}
      <ConfigSection title="Trending Topics" icon={Globe}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <FormField 
            label="Region" 
            description="Target country for trends"
          >
            <select
              value={config.trending_region}
              onChange={(e) => setConfig({...config, trending_region: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="AU">Australia</option>
              <option value="US">United States</option>
              <option value="GB">United Kingdom</option>
              <option value="CA">Canada</option>
              <option value="IN">India</option>
            </select>
          </FormField>
          
          <FormField 
            label="Language" 
            description="Content language"
          >
            <select
              value={config.trending_language}
              onChange={(e) => setConfig({...config, trending_language: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
              <option value="de">German</option>
            </select>
          </FormField>
          
          <FormField 
            label="Max Topics" 
            description="Number of topics to fetch"
          >
            <input
              type="number"
              min="5"
              max="50"
              value={config.max_topics}
              onChange={(e) => setConfig({...config, max_topics: parseInt(e.target.value)})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </FormField>
        </div>
      </ConfigSection>

      {/* Script Generation Section */}
      <ConfigSection title="Script Generation" icon={Mic}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField 
            label="AI Model" 
            description="OpenAI model to use"
          >
            <select
              value={config.script_model}
              onChange={(e) => setConfig({...config, script_model: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="gpt-4-turbo-preview">GPT-4 Turbo (Best Quality)</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo (Faster)</option>
            </select>
          </FormField>
          
          <FormField 
            label="Creativity Level" 
            description="Temperature for AI generation"
          >
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={config.script_temperature}
              onChange={(e) => setConfig({...config, script_temperature: parseFloat(e.target.value)})}
              className="w-full"
            />
            <div className="text-xs text-gray-500 mt-1">
              Current: {config.script_temperature} (0 = Conservative, 1 = Creative)
            </div>
          </FormField>
          
          <FormField 
            label="Script Tone" 
            description="Overall tone of the content"
          >
            <select
              value={config.script_tone}
              onChange={(e) => setConfig({...config, script_tone: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="energetic">Energetic & Engaging</option>
              <option value="professional">Professional</option>
              <option value="casual">Casual & Friendly</option>
              <option value="dramatic">Dramatic & Intense</option>
            </select>
          </FormField>
          
          <FormField 
            label="Language Style" 
            description="Language for the script"
          >
            <select
              value={config.script_language}
              onChange={(e) => setConfig({...config, script_language: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="english">English</option>
              <option value="hinglish">Hinglish (Hindi + English)</option>
            </select>
          </FormField>
        </div>
      </ConfigSection>

      {/* Video Settings Section */}
      <ConfigSection title="Video Settings" icon={Video}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <FormField 
            label="Resolution" 
            description="Video dimensions"
          >
            <select
              value={config.video_resolution}
              onChange={(e) => setConfig({...config, video_resolution: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="1080x1920">1080x1920 (Shorts)</option>
              <option value="1920x1080">1920x1080 (Landscape)</option>
              <option value="1080x1080">1080x1080 (Square)</option>
            </select>
          </FormField>
          
          <FormField 
            label="Frame Rate" 
            description="Frames per second"
          >
            <select
              value={config.video_fps}
              onChange={(e) => setConfig({...config, video_fps: parseInt(e.target.value)})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="24">24 FPS</option>
              <option value="30">30 FPS</option>
              <option value="60">60 FPS</option>
            </select>
          </FormField>
          
          <FormField 
            label="Target Duration" 
            description="Video length in seconds"
          >
            <input
              type="number"
              min="15"
              max="300"
              value={config.video_duration}
              onChange={(e) => setConfig({...config, video_duration: parseInt(e.target.value)})}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
            />
          </FormField>
        </div>
      </ConfigSection>

      {/* YouTube Upload Section */}
      <ConfigSection title="YouTube Upload" icon={Youtube}>
        <div className="space-y-4">
          <FormField 
            label="Auto Upload" 
            description="Automatically upload generated videos to YouTube"
          >
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={config.auto_upload}
                onChange={(e) => setConfig({...config, auto_upload: e.target.checked})}
                className="rounded"
              />
              <span className="text-sm">Enable automatic upload</span>
            </label>
          </FormField>
          
          {config.auto_upload && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pl-6">
              <FormField 
                label="Privacy Setting" 
                description="Default video privacy"
              >
                <select
                  value={config.video_privacy}
                  onChange={(e) => setConfig({...config, video_privacy: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="private">Private</option>
                  <option value="unlisted">Unlisted</option>
                  <option value="public">Public</option>
                </select>
              </FormField>
              
              <FormField 
                label="Auto Thumbnail" 
                description="Generate custom thumbnails"
              >
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={config.auto_thumbnail}
                    onChange={(e) => setConfig({...config, auto_thumbnail: e.target.checked})}
                    className="rounded"
                  />
                  <span className="text-sm">Auto-generate thumbnails</span>
                </label>
              </FormField>
            </div>
          )}
        </div>
      </ConfigSection>

      {/* Voice Settings Section */}
      <ConfigSection title="Voice & Audio Settings" icon={Mic}>
        <div className="space-y-4">
          <FormField 
            label="ElevenLabs Voice" 
            description="Select voice for video narration"
          >
            {loadingVoices ? (
              <div className="flex items-center py-2">
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Loading voices...
              </div>
            ) : (
              <select
                value={config.voice_id}
                onChange={(e) => {
                  const selectedVoice = availableVoices.find(v => v.voice_id === e.target.value);
                  handleVoiceChange(e.target.value, selectedVoice?.name || 'Unknown');
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="default">Default Voice</option>
                {availableVoices.map(voice => (
                  <option key={voice.voice_id} value={voice.voice_id}>
                    {voice.name} - {voice.labels?.accent || 'Unknown'} {voice.labels?.gender || ''} 
                    {voice.labels?.age ? ` (${voice.labels.age})` : ''}
                  </option>
                ))}
              </select>
            )}
          </FormField>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <FormField 
              label="Voice Stability" 
              description="Voice consistency (0-1)"
            >
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={config.voice_stability}
                onChange={(e) => setConfig({...config, voice_stability: parseFloat(e.target.value)})}
                className="w-full"
              />
              <div className="text-xs text-gray-500 mt-1">
                Current: {config.voice_stability}
              </div>
            </FormField>

            <FormField 
              label="Voice Similarity" 
              description="Voice clarity (0-1)"
            >
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={config.voice_similarity}
                onChange={(e) => setConfig({...config, voice_similarity: parseFloat(e.target.value)})}
                className="w-full"
              />
              <div className="text-xs text-gray-500 mt-1">
                Current: {config.voice_similarity}
              </div>
            </FormField>

            <FormField 
              label="Voice Style" 
              description="Expressiveness (0-1)"
            >
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={config.voice_style}
                onChange={(e) => setConfig({...config, voice_style: parseFloat(e.target.value)})}
                className="w-full"
              />
              <div className="text-xs text-gray-500 mt-1">
                Current: {config.voice_style}
              </div>
            </FormField>
          </div>

          <FormField 
            label="Enhanced Language Options" 
            description="Script language and style"
          >
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <select
                value={config.script_language}
                onChange={(e) => setConfig({...config, script_language: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="english">🇺🇸 English</option>
                <option value="hinglish">🇮🇳 Hinglish (Hindi + English Mix)</option>
                <option value="hindi">🇮🇳 Hindi</option>
                <option value="spanish">🇪🇸 Spanish</option>
                <option value="french">🇫🇷 French</option>
                <option value="german">🇩🇪 German</option>
                <option value="italian">🇮🇹 Italian</option>
                <option value="portuguese">🇵🇹 Portuguese</option>
                <option value="russian">🇷🇺 Russian</option>
                <option value="japanese">🇯🇵 Japanese</option>
                <option value="korean">🇰🇷 Korean</option>
                <option value="chinese">🇨🇳 Chinese</option>
              </select>
              
              <select
                value={config.script_tone}
                onChange={(e) => setConfig({...config, script_tone: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="energetic">⚡ Energetic & Viral</option>
                <option value="professional">💼 Professional</option>
                <option value="casual">😊 Casual & Friendly</option>
                <option value="dramatic">🎭 Dramatic & Intense</option>
                <option value="educational">📚 Educational</option>
                <option value="funny">😂 Funny & Humorous</option>
                <option value="mysterious">🔍 Mysterious</option>
              </select>
            </div>
          </FormField>
        </div>
      </ConfigSection>

      {/* YouTube Channels Section */}
      <ConfigSection title="YouTube Channel Management" icon={Youtube}>
        <div className="space-y-4">
          <FormField 
            label="Upload Channel" 
            description="Select which YouTube channel to upload videos to"
          >
            {loadingChannels ? (
              <div className="flex items-center py-2">
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
                Loading channels...
              </div>
            ) : (
              <div className="space-y-3">
                <select
                  value={config.default_channel}
                  onChange={(e) => setConfig({...config, default_channel: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="">Select Default Channel</option>
                  {youtubeChannels.map(channel => (
                    <option key={channel.id} value={channel.id}>
                      {channel.title} ({channel.subscriber_count} subscribers)
                      {channel.is_default ? ' - Current' : ''}
                    </option>
                  ))}
                </select>
                
                <div className="bg-gray-50 p-3 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="text-sm font-medium text-gray-700">Available Channels:</h4>
                    <div className="flex space-x-2">
                      <button
                        onClick={refreshChannels}
                        disabled={loadingChannels}
                        className="px-3 py-1 text-xs bg-gray-200 hover:bg-gray-300 rounded-lg disabled:opacity-50 flex items-center"
                      >
                        <RotateCcw className="w-3 h-3 mr-1" />
                        Refresh
                      </button>
                      <button
                        onClick={handleAddNewChannel}
                        className="px-3 py-1 text-xs bg-green-600 hover:bg-green-700 text-white rounded-lg flex items-center"
                      >
                        <Plus className="w-3 h-3 mr-1" />
                        Add Channel
                      </button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {youtubeChannels.map(channel => (
                      <div key={channel.id} className="flex items-center justify-between py-2 px-3 bg-white rounded border">
                        <div>
                          <div className="font-medium text-gray-900">{channel.title}</div>
                          <div className="text-xs text-gray-500">
                            {channel.subscriber_count} subscribers • ID: {channel.id}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          {channel.is_default && (
                            <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded">Default</span>
                          )}
                          <button
                            onClick={() => handleSetActiveChannel(channel.id)}
                            className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded hover:bg-blue-200"
                          >
                            Select
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                <div className="bg-blue-50 p-3 rounded-lg">
                  <p className="text-sm text-blue-800">
                    💡 <strong>How to add a new channel:</strong> Click "Add Channel" button above to authenticate with Google and grant access to your YouTube channels.
                  </p>
                </div>
              </div>
            )}
          </FormField>
        </div>
      </ConfigSection>

      {/* Save Status */}
      {saved && (
        <div className="fixed bottom-4 right-4 bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg">
          ✓ Settings saved successfully!
        </div>
      )}

      {/* Auth Success Status */}
      {authSuccess && (
        <div className="fixed bottom-4 right-4 bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg">
          ✓ YouTube channel authenticated successfully!
        </div>
      )}

      {/* YouTube Auth Modal */}
      <YouTubeAuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onSuccess={handleAuthSuccess}
        userId={userId}
      />
    </div>
  );
};

export default Settings;