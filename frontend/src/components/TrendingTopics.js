import React, { useState, useEffect } from 'react';
import { TrendingUp, Flame, Clock, BarChart3, RefreshCw } from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || '';

const TrendingTopics = () => {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);

  useEffect(() => {
    fetchTrends();
  }, []);

  const fetchTrends = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/trends`);
      if (!response.ok) throw new Error('Failed to fetch trends');
      const data = await response.json();
      setTopics(data.topics || []);
      setLastUpdated(new Date());
    } catch (error) {
      console.error('Error fetching trends:', error);
      alert('Failed to fetch trends: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const generateFromTopic = async (topic) => {
    try {
      const response = await fetch(`${API_BASE}/api/automation/trigger`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          config: {
            language: 'english',
            upload_to_youtube: false,
            custom_topic: topic.query
          }
        })
      });
      if (!response.ok) throw new Error('Automation failed to start');
      alert('Automation started with selected topic!');
    } catch (error) {
      console.error('Error starting automation:', error);
      alert('Failed to start automation: ' + error.message);
    }
  };

  const TopicCard = ({ topic, index }) => {
    const viralityColor = topic.virality_score > 70 ? 'text-red-500' : 
                         topic.virality_score > 40 ? 'text-orange-500' : 
                         'text-gray-500';
    
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center space-x-2">
            <span className="text-lg font-bold text-gray-400">#{index + 1}</span>
            <div className={`p-1 rounded-full ${viralityColor.replace('text-', 'bg-').replace('500', '100')}`}>
              <Flame className={`w-4 h-4 ${viralityColor}`} />
            </div>
          </div>
          <span className={`text-sm font-medium ${viralityColor}`}>
            {topic.virality_score}/100
          </span>
        </div>
        
        <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
          {topic.query}
        </h3>
        
        <div className="space-y-2 text-xs text-gray-500 mb-4">
          <div className="flex items-center justify-between">
            <span>Search Volume:</span>
            <span className="font-medium">{topic.search_volume?.toLocaleString() || 'N/A'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Category:</span>
            <span className="font-medium">{topic.category || 'General'}</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Status:</span>
            <span className={`font-medium ${topic.status === 'rising' ? 'text-green-600' : 'text-gray-600'}`}>
              {topic.status || 'Stable'}
            </span>
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <button
            onClick={() => setSelectedTopic(topic)}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
          >
            View Details
          </button>
          <button
            onClick={() => generateFromTopic(topic)}
            className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
          >
            Generate Video
          </button>
        </div>
      </div>
    );
  };

  const TopicModal = ({ topic, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-xl font-bold text-gray-900">{topic.query}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          
          {/* Topic Analytics */}
          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {topic.search_volume?.toLocaleString() || 'N/A'}
              </div>
              <div className="text-sm text-blue-700">Search Volume</div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {topic.virality_score}/100
              </div>
              <div className="text-sm text-orange-700">Virality Score</div>
            </div>
          </div>
          
          {/* Breakdown Info */}
          {topic.breakdown && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-3">Analysis Breakdown</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Trend Direction:</span>
                  <span className="font-medium">{topic.breakdown.trend_direction || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Content Freshness:</span>
                  <span className="font-medium">{topic.breakdown.content_freshness || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">News Coverage:</span>
                  <span className="font-medium">
                    {topic.breakdown.has_news_coverage ? 'Yes' : 'No'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Related Queries:</span>
                  <span className="font-medium">
                    {topic.breakdown.trend_breakdown?.length || 0}
                  </span>
                </div>
              </div>
            </div>
          )}
          
          {/* Related Queries */}
          {topic.breakdown?.trend_breakdown && (
            <div className="mb-6">
              <h3 className="font-semibold text-gray-900 mb-3">Related Searches</h3>
              <div className="space-y-1">
                {topic.breakdown.trend_breakdown.slice(0, 5).map((query, index) => (
                  <div key={index} className="text-sm text-gray-600 bg-gray-50 px-3 py-1 rounded">
                    {query}
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* Actions */}
          <div className="flex justify-end space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
            >
              Close
            </button>
            <button
              onClick={() => {
                generateFromTopic(topic);
                onClose();
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Generate Video
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Trending Topics</h1>
          <p className="text-gray-600">Discover what's trending and create viral content</p>
        </div>
        
        <button
          onClick={fetchTrends}
          disabled={loading}
          className="flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <TrendingUp className="w-5 h-5 text-blue-600 mr-2" />
            <div>
              <div className="text-lg font-bold text-gray-900">{topics.length}</div>
              <div className="text-xs text-gray-500">Total Topics</div>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <Flame className="w-5 h-5 text-red-600 mr-2" />
            <div>
              <div className="text-lg font-bold text-gray-900">
                {topics.filter(t => t.virality_score > 70).length}
              </div>
              <div className="text-xs text-gray-500">High Viral Potential</div>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <BarChart3 className="w-5 h-5 text-green-600 mr-2" />
            <div>
              <div className="text-lg font-bold text-gray-900">
                {Math.round(topics.reduce((acc, t) => acc + (t.virality_score || 0), 0) / topics.length) || 0}
              </div>
              <div className="text-xs text-gray-500">Avg Virality Score</div>
            </div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <Clock className="w-5 h-5 text-purple-600 mr-2" />
            <div>
              <div className="text-lg font-bold text-gray-900">
                {lastUpdated ? lastUpdated.toLocaleTimeString() : '--:--'}
              </div>
              <div className="text-xs text-gray-500">Last Updated</div>
            </div>
          </div>
        </div>
      </div>

      {/* Topics Grid */}
      {loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : topics.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {topics.map((topic, index) => (
            <TopicCard key={index} topic={topic} index={index} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <TrendingUp className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No trending topics available</h3>
          <p className="mt-1 text-sm text-gray-500">
            Click refresh to fetch the latest trending topics.
          </p>
        </div>
      )}

      {/* Topic Detail Modal */}
      {selectedTopic && (
        <TopicModal
          topic={selectedTopic}
          onClose={() => setSelectedTopic(null)}
        />
      )}
    </div>
  );
};

export default TrendingTopics;