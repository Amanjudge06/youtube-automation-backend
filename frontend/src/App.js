import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { supabase } from './supabaseClient';
import Auth from './components/Auth';
import Dashboard from './components/Dashboard';
import VideoLibrary from './components/VideoLibrary';
import TrendingTopics from './components/TrendingTopics';
import Settings from './components/Settings';
import Logs from './components/Logs';
import Optimization from './components/Optimization';
import ScheduleManager from './components/ScheduleManager';
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
  Calendar
} from 'lucide-react';

const API_BASE = '/api';

function App() {
  const [session, setSession] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [status, setStatus] = useState({
    running: false,
    current_step: '',
    progress: 0,
    logs: [],
    last_run: null,
    error: null
  });

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  // Fetch status periodically
  useEffect(() => {
    if (!session) return;

    const fetchStatus = async () => {
      try {
        const response = await axios.get(`${API_BASE}/status`);
        setStatus(response.data);
      } catch (error) {
        console.error('Error fetching status:', error);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 2000); // Poll every 2 seconds
    
    return () => clearInterval(interval);
  }, [session]);

  const handleSignOut = async () => {
    await supabase.auth.signOut();
  };

  if (!session) {
    return <Auth onAuthSuccess={(user) => console.log('User logged in:', user)} />;
  }

  const triggerAutomation = async (config = {}) => {
    try {
      // Optimistically set running state
      setStatus(prev => ({ ...prev, running: true, current_step: 'Starting...' }));
      
      await axios.post(`${API_BASE}/automation/trigger`, {
        config: {
          language: 'english',
          trending_region: 'AU',
          script_tone: 'energetic',
          upload_to_youtube: false,
          ...config  // config overrides defaults (including upload_to_youtube)
        },
        user_id: session?.user?.id
      });
    } catch (error) {
      console.error('Error triggering automation:', error);
      // Revert running state on error
      setStatus(prev => ({ ...prev, running: false, current_step: 'Failed' }));
      
      const errorMessage = error.response?.data?.detail || error.message || "Unknown error";
      alert(`Failed to start automation: ${errorMessage}`);
    }
  };

  const stopAutomation = async () => {
    try {
      await axios.get(`${API_BASE}/automation/stop`);
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
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Youtube className="h-8 w-8 text-red-600 mr-3" />
              <h1 className="text-xl font-bold text-gray-900">Snip-Z</h1>
            </div>
            
            {/* Status Indicator */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-3 h-3 rounded-full ${status.running ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`}></div>
                <span className="text-sm text-gray-600">
                  {status.running ? 'Running' : 'Idle'}
                </span>
              </div>

              <button
                onClick={handleSignOut}
                className="p-2 text-gray-500 hover:text-red-600 transition-colors"
                title="Sign Out"
              >
                <LogOut className="w-5 h-5" />
              </button>
              
              {/* Quick Actions */}
              <div className="flex space-x-2">
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

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-12 gap-8">
          {/* Sidebar Navigation */}
          <nav className="col-span-2">
            <ul className="space-y-2">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <li key={item.id}>
                    <button
                      onClick={() => setActiveTab(item.id)}
                      className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-lg transition-colors ${
                        activeTab === item.id
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                      }`}
                    >
                      <Icon className="w-5 h-5 mr-2" />
                      {item.name}
                    </button>
                  </li>
                );
              })}
            </ul>
          </nav>

          {/* Main Content */}
          <main className="col-span-10">
            {activeTab === 'dashboard' && (
              <Dashboard 
                status={status} 
                onTriggerAutomation={triggerAutomation}
                onStopAutomation={stopAutomation}
              />
            )}
            {activeTab === 'schedules' && <ScheduleManager userId={session?.user?.id || 'demo_user'} />}
            {activeTab === 'videos' && <VideoLibrary />}
            {activeTab === 'trending' && <TrendingTopics />}
            {activeTab === 'optimization' && <Optimization />}
            {activeTab === 'settings' && <Settings />}
            {activeTab === 'logs' && <Logs />}
          </main>
        </div>
      </div>
    </div>
  );
}

export default App;