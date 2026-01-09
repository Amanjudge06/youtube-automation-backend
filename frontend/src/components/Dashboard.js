import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Play, 
  Square, 
  Clock, 
  Target, 
  Video, 
  Youtube,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Settings
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || '';

const Dashboard = ({ status, onTriggerAutomation, onStopAutomation }) => {
  // Helper to determine which step is active based on current_step text
  const getActiveStep = (currentStepText) => {
    if (!currentStepText) return -1;
    const text = currentStepText.toLowerCase();
    if (text.includes('trending') || (text.includes('topic') && text.includes('fetch'))) return 0;
    if (text.includes('research')) return 1;
    if (text.includes('script') || text.includes('generating script')) return 2;
    if (text.includes('voiceover') || text.includes('voice') || text.includes('subtitle')) return 3;
    if (text.includes('image') || text.includes('collecting')) return 4;
    if (text.includes('video') || text.includes('assembling') || text.includes('upload')) return 5;
    if (text.includes('completed') || text.includes('success')) return 6;
    return -1;
  };

  const [config, setConfig] = useState({
    language: 'english',
    upload_to_youtube: false,
    trending_region: 'US',
    script_tone: 'energetic',
    custom_topic: ''
  });

  const [recentVideos, setRecentVideos] = useState([]);
  const [stats, setStats] = useState({
    total_videos: 0,
    success_rate: 0,
    avg_duration: 0
  });

  useEffect(() => {
    // Fetch recent videos and stats
    const fetchData = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/videos`);
        if (!response.ok) throw new Error('Failed to fetch videos');
        const data = await response.json();
        setRecentVideos(data.videos?.slice(0, 5) || []); // Show only last 5
        setStats({
          total_videos: data.total || 0,
          success_rate: 95, // Mock data
          avg_duration: 58 // Mock data
        });
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setRecentVideos([]);
      }
    };

    fetchData();

    // Poll for status updates when automation is running
    let pollInterval;
    if (status.running) {
      pollInterval = setInterval(async () => {
        try {
          const response = await fetch(`${API_BASE}/api/status`);
          if (response.ok) {
            const data = await response.json();
            // Status updates will come from parent via onTriggerAutomation
          }
        } catch (error) {
          console.error('Error polling status:', error);
        }
      }, 2000); // Poll every 2 seconds
    }

    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [status.running]); // Refresh when automation status changes

  const StatCard = ({ title, value, icon: Icon, color = "blue", subtitle }) => (
    <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className={`text-2xl font-bold text-${color}-600`}>{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <div className={`p-3 bg-${color}-100 rounded-lg`}>
          <Icon className={`w-6 h-6 text-${color}-600`} />
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-4 md:space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:justify-between md:items-center space-y-2 md:space-y-0">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold text-gray-900">Snip-Z Dashboard</h1>
          <p className="text-sm md:text-base text-gray-600">AI-powered YouTube Shorts automation</p>
        </div>
      </div>

      {/* Custom Topic Section */}
      <div className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl p-4 md:p-6 border border-purple-200 shadow-sm">
        <div className="flex items-center space-x-2 mb-3 md:mb-4">
          <Target className="w-5 h-5 text-purple-600" />
          <h2 className="text-base md:text-lg font-semibold text-gray-900">Create Custom Video</h2>
        </div>
        <div className="flex flex-col md:flex-row md:items-center space-y-3 md:space-y-0 md:space-x-3">
          <input
            type="text"
            value={config.custom_topic}
            onChange={(e) => setConfig({...config, custom_topic: e.target.value})}
            placeholder="Enter topic (e.g., 'History of Pizza')..."
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
          <button
            onClick={() => onTriggerAutomation({...config, custom_topic: config.custom_topic})}
            disabled={status.running || !config.custom_topic.trim()}
            className="w-full md:w-auto flex items-center justify-center px-6 py-2.5 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-medium shadow-sm hover:shadow-md"
          >
            <Play className="w-4 h-4 mr-2" />
            Generate Video
          </button>
        </div>
        <p className="text-xs text-gray-600 mt-2">Or use auto-generation from trending topics below</p>
      </div>

      {/* Quick Start with Trending Topics */}
      <div className="bg-white rounded-xl p-4 md:p-6 border border-gray-200 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4 space-y-3 md:space-y-0">
          <h2 className="text-base md:text-lg font-semibold text-gray-900">Auto-Generate from Trends</h2>
        </div>
        
        {/* Advanced Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-700 block">Language</label>
            <select
              value={config.language}
              onChange={(e) => setConfig({...config, language: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="english">English</option>
              <option value="hinglish">Hinglish</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-700 block">Trending Region</label>
            <select
              value={config.trending_region}
              onChange={(e) => setConfig({...config, trending_region: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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

          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-700 block">Tone</label>
            <select
              value={config.script_tone}
              onChange={(e) => setConfig({...config, script_tone: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="energetic">Energetic</option>
              <option value="professional">Professional</option>
              <option value="casual">Casual</option>
              <option value="dramatic">Dramatic</option>
            </select>
          </div>

          <div className="space-y-1">
            <label className="text-xs font-medium text-gray-700 block">Upload</label>
            <label className="flex items-center h-[38px] px-3 py-2 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-50">
              <input
                type="checkbox"
                checked={config.upload_to_youtube}
                onChange={(e) => setConfig({...config, upload_to_youtube: e.target.checked})}
                className="rounded text-blue-600 focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-sm ml-2">Auto Upload</span>
            </label>
          </div>
        </div>

        <button
          onClick={() => onTriggerAutomation({...config, custom_topic: ''})}
          disabled={status.running}
          className="w-full md:w-auto flex items-center justify-center mt-4 px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 font-medium shadow-sm hover:shadow-md"
        >
          <TrendingUp className="w-4 h-4 mr-2" />
          Start Auto-Generation
        </button>
      </div>

      {/* Status Bar */}
      {status.running && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-4 md:p-6 shadow-md">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4 space-y-2 md:space-y-0">
            <div className="flex items-center space-x-3">
              <div className="relative">
                <Activity className="w-6 h-6 text-blue-600 animate-pulse" />
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-ping"></div>
              </div>
              <div>
                <span className="font-semibold text-blue-900 text-lg">Automation Running</span>
                <p className="text-xs text-blue-600 mt-0.5">Processing your video...</p>
              </div>
            </div>
            <button
              onClick={onStopAutomation}
              className="flex items-center justify-center px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all duration-200 text-sm font-medium shadow-sm hover:shadow-md"
            >
              <Square className="w-4 h-4 mr-2" />
              Stop Process
            </button>
          </div>
          
          <div className="space-y-3">
            {/* Current Step */}
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-blue-800">{status.current_step || 'Processing...'}</p>
              <span className="text-sm font-bold text-blue-900">{Math.round(status.progress || 0)}%</span>
            </div>
            
            {/* Progress Bar */}
            <div className="relative w-full bg-blue-100 rounded-full h-4 overflow-hidden shadow-inner">
              <div 
                className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-700 ease-out flex items-center justify-end"
                style={{ width: `${Math.max(status.progress || 0, 2)}%` }}
              >
                <div className="absolute inset-0 bg-white opacity-20 animate-shimmer"></div>
              </div>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xs font-semibold text-blue-900 mix-blend-difference">
                  {Math.round(status.progress || 0)}%
                </span>
              </div>
            </div>
            
            {/* Progress Steps Indicator - Based on actual backend steps */}
            <div className="grid grid-cols-6 gap-1 mt-2">
              {[
                { name: 'Trending', range: [0, 16] },
                { name: 'Research', range: [17, 33] },
                { name: 'Script', range: [34, 55] },
                { name: 'Voice', range: [56, 70] },
                { name: 'Images', range: [71, 85] },
                { name: 'Video', range: [86, 100] }
              ].map((step, idx) => {
                const progress = status.progress || 0;
                const activeStep = getActiveStep(status.current_step);
                const isComplete = progress > step.range[1];
                const isCurrent = activeStep === idx || (progress >= step.range[0] && progress <= step.range[1]);
                
                return (
                  <div key={step.name} className="text-center">
                    <div className={`h-1.5 rounded-full transition-all duration-500 ${
                      isComplete ? 'bg-green-500' : isCurrent ? 'bg-blue-500 animate-pulse' : 'bg-gray-300'
                    }`}></div>
                    <p className={`text-xs mt-1 transition-colors ${
                      isComplete ? 'text-green-600 font-medium' : isCurrent ? 'text-blue-600 font-medium' : 'text-gray-400'
                    }`}>{step.name}</p>
                  </div>
                );
              })}
            </div>
            
            {/* Show recent logs */}
            {status.logs && status.logs.length > 0 && (
              <div className="mt-4 bg-white rounded-lg p-3 max-h-40 overflow-y-auto shadow-sm border border-blue-100">
                <p className="text-xs font-semibold text-gray-700 mb-2 flex items-center">
                  <span className="inline-block w-2 h-2 bg-blue-500 rounded-full mr-2 animate-pulse"></span>
                  Activity Log
                </p>
                <div className="space-y-1.5">
                  {status.logs.slice(-5).map((log, idx) => (
                    <p key={idx} className="text-xs text-gray-600 pl-4 border-l-2 border-blue-200 py-0.5">{log}</p>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Success Message with YouTube Link */}
      {!status.running && status.progress === 100 && status.youtube_url && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <span className="font-medium text-green-900">Video Created & Uploaded Successfully!</span>
          </div>
          <p className="text-sm text-green-700 mb-3">
            Your video has been generated and uploaded to YouTube.
          </p>
          <a
            href={status.youtube_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            <Youtube className="w-4 h-4 mr-2" />
            Watch on YouTube
          </a>
        </div>
      )}

      {/* Success Message without YouTube */}
      {!status.running && status.progress === 100 && !status.youtube_url && status.video_path && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center space-x-2 mb-2">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <span className="font-medium text-green-900">Video Created Successfully!</span>
          </div>
          <p className="text-sm text-green-700">
            Your video has been generated and saved locally.
          </p>
        </div>
      )}

      {/* Error Display */}
      {status.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-5 h-5 text-red-600" />
            <span className="font-medium text-red-900">Error</span>
          </div>
          <p className="text-sm text-red-700 mt-1">{status.error}</p>
        </div>
      )}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <StatCard
          title="Total Videos"
          value={stats.total_videos}
          icon={Video}
          color="blue"
          subtitle="Generated videos"
        />
        <StatCard
          title="Success Rate"
          value={`${stats.success_rate}%`}
          icon={CheckCircle}
          color="green"
          subtitle="Successful generations"
        />
        <StatCard
          title="Avg Duration"
          value={`${stats.avg_duration}s`}
          icon={Clock}
          color="purple"
          subtitle="Average video length"
        />
        <StatCard
          title="Trending Score"
          value="8.5/10"
          icon={TrendingUp}
          color="orange"
          subtitle="Algorithm optimization"
        />
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Videos */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">Recent Videos</h3>
          </div>
          <div className="p-6 space-y-4">
            {recentVideos.length > 0 ? (
              recentVideos.map((video, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900 text-sm truncate">{video.title}</h4>
                    <p className="text-xs text-gray-500 mt-1">
                      {video.topic} • {Math.round(video.duration)}s • {video.created_at}
                    </p>
                  </div>
                  <div className="flex items-center space-x-2">
                    {video.youtube_url && (
                      <Youtube className="w-4 h-4 text-red-600" />
                    )}
                    <button className="text-blue-600 hover:text-blue-800 text-xs">
                      View
                    </button>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-500 text-center py-4">No videos generated yet</p>
            )}
          </div>
        </div>

        {/* System Status */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-semibold text-gray-900">System Status</h3>
          </div>
          <div className="p-6 space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">API Status</span>
              <span className="flex items-center text-green-600">
                <CheckCircle className="w-4 h-4 mr-1" />
                Online
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">YouTube API</span>
              <span className="flex items-center text-green-600">
                <CheckCircle className="w-4 h-4 mr-1" />
                Connected
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">OpenAI API</span>
              <span className="flex items-center text-green-600">
                <CheckCircle className="w-4 h-4 mr-1" />
                Active
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">ElevenLabs API</span>
              <span className="flex items-center text-green-600">
                <CheckCircle className="w-4 h-4 mr-1" />
                Active
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Last Run</span>
              <span className="text-sm text-gray-500">
                {status.last_run ? new Date(status.last_run).toLocaleString() : 'Never'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-500 hover:bg-blue-50 transition-colors">
              <Target className="w-5 h-5 text-gray-400 mr-2" />
              <span className="text-sm text-gray-600">Generate from Topic</span>
            </button>
            <button className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-green-500 hover:bg-green-50 transition-colors">
              <TrendingUp className="w-5 h-5 text-gray-400 mr-2" />
              <span className="text-sm text-gray-600">Use Trending Topic</span>
            </button>
            <button className="flex items-center justify-center p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-purple-500 hover:bg-purple-50 transition-colors">
              <Settings className="w-5 h-5 text-gray-400 mr-2" />
              <span className="text-sm text-gray-600">Custom Settings</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;