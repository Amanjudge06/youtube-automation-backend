import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import Dashboard from './Dashboard';
import VideoLibrary from './VideoLibrary';
import TrendingTopics from './TrendingTopics';
import SettingsNew from './SettingsNew';
import Logs from './Logs';
import Optimization from './Optimization';
import ScheduleManager from './ScheduleManager';
import { 
  Home, 
  Video, 
  TrendingUp, 
  Settings as SettingsIcon, 
  FileText,
  Play,
  Square,
  Youtube,
  Brain,
  LogOut,
  Calendar,
  User
} from 'lucide-react';

const API_BASE = '/api';

// Configure axios to include auth token
axios.interceptors.request.use((config) => {
  const session = JSON.parse(localStorage.getItem('supabase.auth.token') || '{}');
  if (session?.currentSession?.access_token) {
    config.headers.Authorization = `Bearer ${session.currentSession.access_token}`;
  }
  return config;
});

function MainApp() {
  const { user, signOut, session } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [status, setStatus] = useState({
    running: false,
    current_step: '',
    progress: 0,
    logs: [],
    last_run: null,
    error: null
  });
  const [userInfo, setUserInfo] = useState(null);

  // Fetch user info
  useEffect(() => {
    const fetchUserInfo = async () => {
      if (!session?.access_token) return;
      
      try {
        const response = await axios.get(`${API_BASE}/auth/me`, {
          headers: { Authorization: `Bearer ${session.access_token}` }
        });
        setUserInfo(response.data);
      } catch (error) {
        console.error('Error fetching user info:', error);
      }
    };

    fetchUserInfo();
  }, [session]);

  // Fetch status periodically with auth token
  useEffect(() => {
    if (!session?.access_token) return;

    const fetchStatus = async () => {
      try {
        const response = await axios.get(`${API_BASE}/status`, {
          headers: { Authorization: `Bearer ${session.access_token}` }
        });
        const data = response.data;
        
        // Keep progress at 100% if automation just completed
        if (!data.running && data.progress === 0 && status.running) {
          setStatus(prev => ({ ...prev, running: false }));
        } else {
          setStatus(data);
        }
      } catch (error) {
        console.error('Error fetching status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 1000);
    
    return () => clearInterval(interval);
  }, [session, status.running]);

  const triggerAutomation = async (config = {}) => {
    try {
      setStatus(prev => ({ ...prev, running: true, current_step: 'Starting...' }));
      
      await axios.post(`${API_BASE}/automation/trigger`, {
        config: {
          language: 'english',
          trending_region: 'AU',
          script_tone: 'energetic',
          upload_to_youtube: false,
          ...config
        }
      }, {
        headers: { Authorization: `Bearer ${session.access_token}` }
      });
    } catch (error) {
      console.error('Error triggering automation:', error);
      setStatus(prev => ({ ...prev, running: false, current_step: 'Failed' }));
      
      const errorMessage = error.response?.data?.detail || error.message || "Unknown error";
      alert(`Failed to start automation: ${errorMessage}`);
    }
  };

  const stopAutomation = async () => {
    try {
      await axios.get(`${API_BASE}/automation/stop`, {
        headers: { Authorization: `Bearer ${session.access_token}` }
      });
    } catch (error) {
      console.error('Error stopping automation:', error);
    }
  };

  const navigation = [
    { id: 'dashboard', name: 'Dashboard', icon: Home },
    { id: 'schedules', name: 'Schedules', icon: Calendar },
    { id: 'videos', name: 'Video Library', icon: Video },
    { id: 'trending', name: 'Trending Topics', icon: TrendingUp },
    { id: 'optimization', name: 'AI Optimization', icon: Brain },
    { id: 'settings', name: 'Settings', icon: SettingsIcon },
    { id: 'logs', name: 'Logs', icon: FileText },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-14 sm:h-16">
            <div className="flex items-center">
              <Youtube className="h-6 w-6 sm:h-8 sm:w-8 text-red-600 mr-2 sm:mr-3" />
              <div>
                <h1 className="text-lg sm:text-xl font-bold text-gray-900">Snip-Z</h1>
                <p className="text-xs text-gray-500 hidden sm:block">AI YouTube Automation</p>
              </div>
            </div>
            
            {/* Status Indicator & User Menu */}
            <div className="flex items-center space-x-2 sm:space-x-4">
              {/* Usage Info */}
              {userInfo && (
                <div className="hidden lg:flex items-center space-x-2 px-3 py-1.5 bg-purple-50 rounded-lg">
                  <span className="text-xs font-medium text-purple-700">
                    {userInfo.usage?.daily_remaining || 0} videos left today
                  </span>
                </div>
              )}
              
              {/* Status */}
              <div className="hidden md:flex items-center space-x-2">
                <div className={`w-2.5 h-2.5 rounded-full ${status.running ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
                <span className="text-sm text-gray-600">
                  {status.running ? 'Running' : 'Idle'}
                </span>
              </div>

              {/* User Menu */}
              <div className="relative group">
                <button className="flex items-center space-x-2 px-3 py-2 hover:bg-gray-100 rounded-lg transition">
                  <User className="w-5 h-5 text-gray-600" />
                  <span className="hidden sm:inline text-sm text-gray-700">{user?.email}</span>
                </button>
                
                {/* Dropdown */}
                <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-gray-200 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                  <div className="p-2">
                    <button
                      onClick={signOut}
                      className="flex items-center w-full px-3 py-2 text-sm text-gray-700 hover:bg-red-50 hover:text-red-600 rounded-lg transition"
                    >
                      <LogOut className="w-4 h-4 mr-2" />
                      Sign Out
                    </button>
                  </div>
                </div>
              </div>

              {/* Quick Actions - Desktop Only */}
              <div className="hidden lg:flex space-x-2">
                <button
                  onClick={() => triggerAutomation()}
                  disabled={status.running}
                  className="flex items-center px-3 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  <Play className="w-4 h-4 mr-1" />
                  Start
                </button>
                <button
                  onClick={stopAutomation}
                  disabled={!status.running}
                  className="flex items-center px-3 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm"
                >
                  <Square className="w-4 h-4 mr-1" />
                  Stop
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 md:py-8">
        <div className="flex flex-col lg:flex-row gap-4 md:gap-8">
          {/* Sidebar Navigation */}
          <nav className="w-full lg:w-64 flex-shrink-0">
            <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-2">
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-1 gap-1 lg:gap-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`flex flex-col lg:flex-row items-center justify-center lg:justify-start space-y-1 lg:space-y-0 lg:space-x-3 px-3 py-2.5 lg:py-3 text-xs lg:text-sm font-medium rounded-lg transition-all duration-200 ${
                      activeTab === item.id
                        ? 'bg-blue-50 text-blue-700 shadow-sm'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="w-5 h-5 flex-shrink-0" />
                    <span className="lg:inline">{item.name}</span>
                  </button>
                );
              })}
              </div>
            </div>
          </nav>

          {/* Main Content */}
          <main className="flex-1 min-w-0">
            {activeTab === 'dashboard' && (
              <Dashboard 
                status={status} 
                onTriggerAutomation={triggerAutomation}
                onStopAutomation={stopAutomation}
              />
            )}
            {activeTab === 'schedules' && <ScheduleManager userId={user?.id} />}
            {activeTab === 'videos' && <VideoLibrary />}
            {activeTab === 'trending' && <TrendingTopics />}
            {activeTab === 'optimization' && <Optimization />}
            {activeTab === 'settings' && <SettingsNew userId={user?.id} />}
            {activeTab === 'logs' && <Logs />}
          </main>
        </div>
      </div>
    </div>
  );
}

export default MainApp;
