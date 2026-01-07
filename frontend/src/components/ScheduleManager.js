import React, { useState, useEffect, useCallback } from 'react';
import { Clock, Plus, Trash2, Power, PowerOff, Calendar, Globe, Settings as SettingsIcon } from 'lucide-react';
import axios from 'axios';

const API_BASE = '/api';

const ScheduleManager = ({ userId = 'demo_user' }) => {
  const [schedules, setSchedules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddModal, setShowAddModal] = useState(false);
  const [newSchedule, setNewSchedule] = useState({
    schedule_time: '09:00',
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
    config: {
      language: 'english',
      upload_to_youtube: true,
      trending_region: 'US',
      script_tone: 'energetic'
    }
  });

  const fetchSchedules = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE}/schedules?user_id=${userId}`);
      setSchedules(response.data.schedules || []);
    } catch (error) {
      console.error('Error fetching schedules:', error);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    fetchSchedules();
    const interval = setInterval(fetchSchedules, 30000);
    return () => clearInterval(interval);
  }, [fetchSchedules]);

  const createSchedule = async () => {
    try {
      const response = await axios.post(`${API_BASE}/schedules?user_id=${userId}`, newSchedule);
      if (response.data.success) {
        setShowAddModal(false);
        setNewSchedule({
          schedule_time: '09:00',
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
          config: {
            language: 'english',
            upload_to_youtube: true,
            trending_region: 'US',
            script_tone: 'energetic'
          }
        });
        await fetchSchedules();
        alert('Schedule created successfully!');
      }
    } catch (error) {
      console.error('Error creating schedule:', error);
      alert('Failed to create schedule: ' + (error.response?.data?.detail || error.message));
    }
  };

  const deleteSchedule = async (scheduleId) => {
    if (!window.confirm('Are you sure you want to delete this schedule? This action cannot be undone.')) return;
    
    try {
      await axios.delete(`${API_BASE}/schedules/${scheduleId}`);
      await fetchSchedules();
      alert('Schedule deleted successfully');
    } catch (error) {
      console.error('Error deleting schedule:', error);
      alert('Failed to delete schedule: ' + (error.response?.data?.detail || error.message));
    }
  };

  const toggleSchedule = async (scheduleId, currentlyActive) => {
    try {
      await axios.post(`${API_BASE}/schedules/${scheduleId}/toggle?active=${!currentlyActive}`);
      await fetchSchedules();
      const action = currentlyActive ? 'disabled' : 'enabled';
      alert(`Schedule ${action} successfully`);
    } catch (error) {
      console.error('Error toggling schedule:', error);
      alert('Failed to toggle schedule: ' + (error.response?.data?.detail || error.message));
    }
  };

  const formatNextRun = (nextRun) => {
    if (!nextRun) return 'Not scheduled';
    const date = new Date(nextRun);
    return date.toLocaleString();
  };

  const timezones = [
    'UTC',
    'America/New_York',
    'America/Chicago',
    'America/Denver',
    'America/Los_Angeles',
    'Europe/London',
    'Europe/Paris',
    'Asia/Tokyo',
    'Asia/Shanghai',
    'Australia/Sydney'
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Automation Schedules</h2>
          <p className="text-gray-600">Set up automated video creation on autopilot</p>
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <Plus className="w-5 h-5 mr-2" />
          Add Schedule
        </button>
      </div>

      {/* Schedules List */}
      {loading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-gray-600 mt-4">Loading schedules...</p>
        </div>
      ) : schedules.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No schedules yet</h3>
          <p className="text-gray-600 mb-4">Create your first automation schedule to start generating videos automatically</p>
          <button
            onClick={() => setShowAddModal(true)}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-5 h-5 mr-2" />
            Create Schedule
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {schedules.map((schedule) => (
            <div
              key={schedule.id}
              className={`bg-white rounded-lg shadow-sm border-2 p-6 ${
                schedule.active ? 'border-green-500' : 'border-gray-200'
              }`}
            >
              {/* Schedule Header */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Clock className={`w-6 h-6 ${schedule.active ? 'text-green-600' : 'text-gray-400'}`} />
                  <span className="text-2xl font-bold text-gray-900">{schedule.schedule_time}</span>
                </div>
                <button
                  onClick={() => toggleSchedule(schedule.id, schedule.active)}
                  className={`p-2 rounded-lg ${
                    schedule.active 
                      ? 'bg-green-100 text-green-600 hover:bg-green-200' 
                      : 'bg-gray-100 text-gray-400 hover:bg-gray-200'
                  }`}
                  title={schedule.active ? 'Disable' : 'Enable'}
                >
                  {schedule.active ? <Power className="w-5 h-5" /> : <PowerOff className="w-5 h-5" />}
                </button>
              </div>

              {/* Schedule Details */}
              <div className="space-y-3 mb-4">
                <div className="flex items-center text-sm text-gray-600">
                  <Globe className="w-4 h-4 mr-2" />
                  <span>{schedule.timezone}</span>
                </div>
                
                <div className="text-sm">
                  <span className="text-gray-600">Next Run: </span>
                  <span className="font-medium text-gray-900">
                    {formatNextRun(schedule.next_run)}
                  </span>
                </div>

                {schedule.last_run && (
                  <div className="text-sm">
                    <span className="text-gray-600">Last Run: </span>
                    <span className="text-gray-900">
                      {new Date(schedule.last_run).toLocaleString()}
                    </span>
                  </div>
                )}

                <div className="text-sm">
                  <span className="text-gray-600">Runs: </span>
                  <span className="font-medium text-gray-900">{schedule.run_count || 0}</span>
                </div>

                {schedule.last_result && (
                  <div className="text-sm">
                    <span className="text-gray-600">Status: </span>
                    <span className={`font-medium ${
                      schedule.last_result === 'success' ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {schedule.last_result}
                    </span>
                  </div>
                )}
              </div>

              {/* Config Details */}
              <div className="bg-gray-50 rounded p-3 mb-4">
                <div className="flex items-center text-xs text-gray-600 mb-1">
                  <SettingsIcon className="w-3 h-3 mr-1" />
                  Configuration
                </div>
                <div className="text-xs space-y-1">
                  <div>Language: <span className="font-medium">{schedule.config?.language || 'english'}</span></div>
                  <div>Auto Upload: <span className="font-medium">{schedule.config?.upload_to_youtube ? 'Yes' : 'No'}</span></div>
                  <div>Region: <span className="font-medium">{schedule.config?.trending_region || 'US'}</span></div>
                </div>
              </div>

              {/* Actions */}
              <button
                onClick={() => deleteSchedule(schedule.id)}
                className="w-full flex items-center justify-center px-4 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Delete
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Add Schedule Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Add New Schedule</h3>
            
            <div className="space-y-4">
              {/* Time */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Time (24-hour format)
                </label>
                <input
                  type="time"
                  value={newSchedule.schedule_time}
                  onChange={(e) => setNewSchedule({...newSchedule, schedule_time: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>

              {/* Timezone */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Timezone
                </label>
                <select
                  value={newSchedule.timezone}
                  onChange={(e) => setNewSchedule({...newSchedule, timezone: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  {timezones.map(tz => (
                    <option key={tz} value={tz}>{tz}</option>
                  ))}
                </select>
              </div>

              {/* Language */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Language
                </label>
                <select
                  value={newSchedule.config.language}
                  onChange={(e) => setNewSchedule({
                    ...newSchedule,
                    config: {...newSchedule.config, language: e.target.value}
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="english">English</option>
                  <option value="hinglish">Hinglish</option>
                </select>
              </div>

              {/* Auto Upload */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  checked={newSchedule.config.upload_to_youtube}
                  onChange={(e) => setNewSchedule({
                    ...newSchedule,
                    config: {...newSchedule.config, upload_to_youtube: e.target.checked}
                  })}
                  className="rounded mr-2"
                />
                <label className="text-sm text-gray-700">
                  Automatically upload to YouTube
                </label>
              </div>

              {/* Region */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Trending Region
                </label>
                <select
                  value={newSchedule.config.trending_region}
                  onChange={(e) => setNewSchedule({
                    ...newSchedule,
                    config: {...newSchedule.config, trending_region: e.target.value}
                  })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  <option value="US">United States</option>
                  <option value="GB">United Kingdom</option>
                  <option value="IN">India</option>
                  <option value="AU">Australia</option>
                  <option value="CA">Canada</option>
                </select>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => setShowAddModal(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={createSchedule}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Create Schedule
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScheduleManager;
