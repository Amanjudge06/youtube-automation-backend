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

const Dashboard = ({ status, onTriggerAutomation, onStopAutomation }) => {
  const [config, setConfig] = useState({
    language: 'english',
    upload_to_youtube: false,
    trending_region: 'AU',
    script_tone: 'energetic'
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
        const response = await fetch('/api/videos');
        const data = await response.json();
        setRecentVideos(data.videos.slice(0, 5)); // Show only last 5
        setStats({
          total_videos: data.total,
          success_rate: 95, // Mock data
          avg_duration: 58 // Mock data
        });
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      }
    };

    fetchData();

    // Poll for status updates when automation is running
    let pollInterval;
    if (status.running) {
      pollInterval = setInterval(async () => {
        try {
          const response = await fetch('/api/status');
          const data = await response.json();
          // Status updates will come from parent via onTriggerAutomation
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
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Snip-Z Dashboard</h1>
          <p className="text-gray-600">Monitor and control your YouTube automation</p>
        </div>
        
        {/* Advanced Controls */}
        <div className="flex items-center space-x-4">
          <select
            value={config.language}
            onChange={(e) => setConfig({...config, language: e.target.value})}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
          >
            <option value="english">English</option>
            <option value="hinglish">Hinglish</option>
          </select>
          
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={config.upload_to_youtube}
              onChange={(e) => setConfig({...config, upload_to_youtube: e.target.checked})}
              className="rounded"
            />
            <span className="text-sm">Auto Upload</span>
          </label>
          
          <button
            onClick={() => onTriggerAutomation(config)}
            disabled={status.running}
            className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play className="w-4 h-4 mr-2" />
            Start Automation
          </button>
        </div>
      </div>

      {/* Status Bar */}
      {status.running && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Activity className="w-5 h-5 text-blue-600 animate-pulse" />
              <span className="font-medium text-blue-900">Automation Running</span>
            </div>
            <button
              onClick={onStopAutomation}
              className="flex items-center px-3 py-1 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm"
            >
              <Square className="w-4 h-4 mr-1" />
              Stop
            </button>
          </div>
          
          <div className="space-y-2">
            <p className="text-sm font-medium text-blue-700">{status.current_step}</p>
            <div className="w-full bg-blue-200 rounded-full h-3">
              <div 
                className="bg-blue-600 h-3 rounded-full transition-all duration-500 flex items-center justify-end pr-2"
                style={{ width: `${status.progress}%` }}
              >
                <span className="text-xs text-white font-medium">{status.progress}%</span>
              </div>
            </div>
            
            {/* Show recent logs */}
            {status.logs && status.logs.length > 0 && (
              <div className="mt-3 bg-white rounded p-3 max-h-32 overflow-y-auto">
                <p className="text-xs font-medium text-gray-600 mb-1">Recent Activity:</p>
                <div className="space-y-1">
                  {status.logs.slice(-5).map((log, idx) => (
                    <p key={idx} className="text-xs text-gray-700">{log}</p>
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