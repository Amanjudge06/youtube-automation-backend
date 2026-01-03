import React, { useState, useEffect } from 'react';
import { Brain, Settings, CheckCircle, FileText, TrendingUp, Volume2, AlertTriangle, Loader2, GitBranch, Mic } from 'lucide-react';

const Optimization = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [optimizationStatus, setOptimizationStatus] = useState(null);
  const [isApplying, setIsApplying] = useState(false);
  const [channelUrl, setChannelUrl] = useState('');
  const [myChannelInfo, setMyChannelInfo] = useState(null);
  const [useMyChannel, setUseMyChannel] = useState(false);
  const [beforeAfterComparison, setBeforeAfterComparison] = useState(null);
  const [availableVoices, setAvailableVoices] = useState([]);
  const [currentVoice, setCurrentVoice] = useState(null);
  const [isLoadingVoices, setIsLoadingVoices] = useState(false);
  const [showVoiceSelector, setShowVoiceSelector] = useState(false);

  useEffect(() => {
    fetchOptimizationStatus();
    fetchMyChannelInfo();
    fetchAvailableVoices();
    fetchCurrentVoice();
  }, []);

  const fetchOptimizationStatus = async () => {
    try {
      const response = await fetch('/optimization/status');
      if (response.ok) {
        const data = await response.json();
        setOptimizationStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch optimization status:', error);
    }
  };

  const fetchMyChannelInfo = async () => {
    try {
      const response = await fetch('/optimization/my-channel');
      if (response.ok) {
        const data = await response.json();
        if (data.success && data.channel_info) {
          setMyChannelInfo(data.channel_info);
          setUseMyChannel(true);
          setChannelUrl(data.channel_info.channel_url);
        }
      }
    } catch (error) {
      console.error('Failed to fetch my channel info:', error);
    }
  };

  const fetchAvailableVoices = async () => {
    try {
      setIsLoadingVoices(true);
      const response = await fetch('/voices/available');
      if (response.ok) {
        const data = await response.json();
        setAvailableVoices(data.voices);
      }
    } catch (error) {
      console.error('Failed to fetch available voices:', error);
    } finally {
      setIsLoadingVoices(false);
    }
  };

  const fetchCurrentVoice = async () => {
    try {
      const response = await fetch('/voices/current');
      if (response.ok) {
        const data = await response.json();
        setCurrentVoice(data);
      }
    } catch (error) {
      console.error('Failed to fetch current voice:', error);
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
        await fetchCurrentVoice();
        setShowVoiceSelector(false);
        alert(`Voice successfully changed to: ${voiceName}`);
      }
    } catch (error) {
      console.error('Failed to change voice:', error);
      alert('Failed to change voice. Please try again.');
    }
  };

  const analyzeChannel = async () => {
    const urlToAnalyze = useMyChannel && myChannelInfo ? myChannelInfo.channel_url : channelUrl.trim();
    
    if (!urlToAnalyze) {
      alert('Please enter a valid channel URL');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisResults(null);
    
    try {
      const response = await fetch('/optimization/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ channel_url: urlToAnalyze })
      });

      if (response.ok) {
        const data = await response.json();
        setAnalysisResults(data);
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Analysis failed');
      }
    } catch (error) {
      console.error('Analysis failed:', error);
      alert(`Analysis failed: ${error.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const applyOptimizations = async () => {
    if (!analysisResults?.recommendations) {
      alert('No recommendations to apply');
      return;
    }

    setIsApplying(true);
    
    try {
      const response = await fetch('/optimization/apply', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          channel_url: useMyChannel && myChannelInfo ? myChannelInfo.channel_url : channelUrl.trim()
        })
      });

      if (response.ok) {
        const data = await response.json();
        setBeforeAfterComparison(data.before_after_comparison);
        alert('Optimizations applied successfully!');
        await fetchOptimizationStatus(); // Refresh status
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to apply optimizations');
      }
    } catch (error) {
      console.error('Failed to apply optimizations:', error);
      alert(`Failed to apply optimizations: ${error.message}`);
    } finally {
      setIsApplying(false);
    }
  };

  const formatPercentage = (value) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Brain className="w-8 h-8 text-purple-600" />
            <div>
              <h1 className="text-2xl font-bold text-gray-900">AI Content Optimization</h1>
              <p className="text-gray-600 mt-1">Analyze channel performance and optimize content generation</p>
            </div>
          </div>
          {optimizationStatus?.content_optimization?.status === 'active' && (
            <div className="flex items-center space-x-2 text-green-600">
              <CheckCircle className="w-5 h-5" />
              <span className="text-sm font-medium">AI Learning Active</span>
            </div>
          )}
        </div>
      </div>

      {/* Current Optimization Status */}
      {optimizationStatus && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Settings className="w-5 h-5 mr-2 text-gray-600" />
            Current Optimization Settings
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-gray-700 flex items-center">
                <FileText className="w-4 h-4 mr-2" />
                Script Generation
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Hook Style:</span>
                  <span className="font-medium capitalize">{optimizationStatus.script_optimization?.hook_style || 'question_based'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Controversy:</span>
                  <span className="font-medium">{optimizationStatus.script_optimization?.controversy_level || 0.3}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Temperature:</span>
                  <span className="font-medium">{optimizationStatus.script_optimization?.temperature || 0.7}</span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="text-sm font-medium text-gray-700 flex items-center">
                <TrendingUp className="w-4 h-4 mr-2" />
                Trending Weights
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Volume Weight:</span>
                  <span className="font-medium">{formatPercentage(optimizationStatus.trends_optimization?.volume_weight || 0.3)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Velocity Weight:</span>
                  <span className="font-medium">{formatPercentage(optimizationStatus.trends_optimization?.velocity_weight || 0.4)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Recency Weight:</span>
                  <span className="font-medium">{formatPercentage(optimizationStatus.trends_optimization?.recency_weight || 0.3)}</span>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <h3 className="text-sm font-medium text-gray-700 flex items-center">
                <Volume2 className="w-4 h-4 mr-2" />
                Voice Settings
                <button
                  onClick={() => setShowVoiceSelector(!showVoiceSelector)}
                  className="ml-auto px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                >
                  <Mic className="w-3 h-3 inline mr-1" />
                  Change
                </button>
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Voice ID:</span>
                  <span className="font-medium">{currentVoice?.voice_id || optimizationStatus.voice_optimization?.voice_id || 'default'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Stability:</span>
                  <span className="font-medium">{currentVoice?.voice_settings?.stability || optimizationStatus.voice_optimization?.stability || 0.5}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Clarity:</span>
                  <span className="font-medium">{currentVoice?.voice_settings?.similarity_boost || optimizationStatus.voice_optimization?.similarity_boost || 0.75}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Channel Analysis Form */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Channel Analysis</h2>
        <div className="space-y-4">
          {/* My Channel Option */}
          {myChannelInfo && (
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold">
                    {myChannelInfo.channel_title.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{myChannelInfo.channel_title}</h3>
                    <p className="text-sm text-gray-600">
                      {myChannelInfo.subscriber_count.toLocaleString()} subscribers • {myChannelInfo.video_count} videos
                    </p>
                  </div>
                </div>
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useMyChannel}
                    onChange={(e) => {
                      setUseMyChannel(e.target.checked);
                      if (e.target.checked) {
                        setChannelUrl(myChannelInfo.channel_url);
                      } else {
                        setChannelUrl('');
                      }
                    }}
                    className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                  />
                  <span className="text-sm font-medium text-blue-700">Use my channel</span>
                </label>
              </div>
            </div>
          )}
          
          <div>
            <label htmlFor="channelUrl" className="block text-sm font-medium text-gray-700 mb-2">
              {useMyChannel && myChannelInfo ? 'Selected Channel URL' : 'YouTube Channel URL'}
            </label>
            <input
              type="text"
              id="channelUrl"
              value={channelUrl}
              onChange={(e) => {
                setChannelUrl(e.target.value);
                setUseMyChannel(false);
              }}
              placeholder="https://www.youtube.com/@channelname"
              disabled={useMyChannel && myChannelInfo}
              className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent ${
                useMyChannel && myChannelInfo ? 'bg-gray-50 text-gray-600' : ''
              }`}
            />
          </div>
          <button
            onClick={analyzeChannel}
            disabled={isAnalyzing || (!(useMyChannel && myChannelInfo) && !channelUrl.trim())}
            className="w-full bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {useMyChannel && myChannelInfo ? 'Analyzing My Channel...' : 'Analyzing Channel...'}
              </>
            ) : (
              useMyChannel && myChannelInfo ? 'Analyze My Channel' : 'Analyze Channel'
            )}
          </button>
        </div>
      </div>

      {/* Analysis Results */}
      {analysisResults && (
        <div className="space-y-6">
          {/* Performance Metrics */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance Analysis</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">
                  {analysisResults.channel_metrics?.subscriber_count?.toLocaleString() || 'N/A'}
                </div>
                <div className="text-sm text-gray-600">Subscribers</div>
              </div>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {analysisResults.channel_metrics?.total_views?.toLocaleString() || 'N/A'}
                </div>
                <div className="text-sm text-gray-600">Total Views</div>
              </div>
              <div className="bg-yellow-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-yellow-600">
                  {analysisResults.channel_metrics?.video_count?.toLocaleString() || 'N/A'}
                </div>
                <div className="text-sm text-gray-600">Videos</div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">
                  {analysisResults.channel_metrics?.avg_views_per_video?.toLocaleString() || 'N/A'}
                </div>
                <div className="text-sm text-gray-600">Avg Views</div>
              </div>
            </div>
          </div>

          {/* Content Patterns */}
          {analysisResults.content_patterns && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Content Patterns</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-3">Top Topics</h3>
                  <div className="space-y-2">
                    {analysisResults.content_patterns.top_topics?.slice(0, 5).map((topic, index) => (
                      <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span className="text-sm">{topic.topic}</span>
                        <span className="text-sm font-medium text-purple-600">{topic.count} videos</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-3">Performance Insights</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Best Upload Day:</span>
                      <span className="font-medium">{analysisResults.content_patterns.best_upload_day || 'Unknown'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Best Upload Time:</span>
                      <span className="font-medium">{analysisResults.content_patterns.best_upload_time || 'Unknown'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Optimal Video Length:</span>
                      <span className="font-medium">{analysisResults.content_patterns.optimal_length || 'Unknown'}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* AI Recommendations */}
          {analysisResults.recommendations && (
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <AlertTriangle className="w-5 h-5 mr-2 text-yellow-500" />
                AI Optimization Recommendations
              </h2>
              <div className="space-y-4">
                {analysisResults.recommendations.map((rec, index) => (
                  <div key={index} className="border-l-4 border-purple-500 pl-4 py-2">
                    <div className="font-medium text-gray-900">{rec.category}</div>
                    <div className="text-sm text-gray-600 mt-1">{rec.suggestion}</div>
                    <div className="text-xs text-purple-600 mt-1">
                      Impact: {rec.impact} | Confidence: {rec.confidence}
                    </div>
                  </div>
                ))}
              </div>
              
              {/* Apply Changes Button */}
              <div className="mt-6 pt-4 border-t">
                <button
                  onClick={applyOptimizations}
                  disabled={isApplying}
                  className="w-full bg-green-600 text-white px-4 py-3 rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center font-medium"
                >
                  {isApplying ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Applying Optimizations...
                    </>
                  ) : (
                    'Apply All Recommendations'
                  )}
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Voice Selector Modal */}
      {showVoiceSelector && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-96 overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
              <Mic className="w-5 h-5 mr-2" />
              Select ElevenLabs Voice
            </h3>
            
            {isLoadingVoices ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                Loading voices...
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-3 max-h-64 overflow-y-auto">
                {availableVoices.map((voice) => (
                  <div
                    key={voice.voice_id}
                    onClick={() => handleVoiceChange(voice.voice_id, voice.name)}
                    className={`p-3 border rounded-lg cursor-pointer hover:bg-blue-50 ${
                      currentVoice?.voice_id === voice.voice_id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <div>
                        <h4 className="font-medium text-gray-900">{voice.name}</h4>
                        <p className="text-sm text-gray-600">
                          {voice.labels?.accent && `${voice.labels.accent} • `}
                          {voice.labels?.description || 'No description'}
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Age: {voice.labels?.age || 'Unknown'} • Gender: {voice.labels?.gender || 'Unknown'}
                        </p>
                      </div>
                      {currentVoice?.voice_id === voice.voice_id && (
                        <CheckCircle className="w-5 h-5 text-blue-600" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
            
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => setShowVoiceSelector(false)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Before/After Comparison */}
      {beforeAfterComparison && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <GitBranch className="w-5 h-5 mr-2 text-green-600" />
            Optimization Changes Applied
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Before State */}
            <div className="space-y-4">
              <h3 className="text-md font-medium text-gray-700 flex items-center">
                <span className="w-3 h-3 bg-red-500 rounded-full mr-2"></span>
                Before Optimization
              </h3>
              <div className="bg-red-50 p-4 rounded-lg">
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Profile:</span>
                    <span className="font-medium">{beforeAfterComparison.before?.profile?.name || 'Default'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Voice:</span>
                    <span className="font-medium">{beforeAfterComparison.before?.config_snapshot?.voice_settings?.voice_id || 'default'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Updated:</span>
                    <span className="font-medium">{new Date(beforeAfterComparison.before?.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* After State */}
            <div className="space-y-4">
              <h3 className="text-md font-medium text-gray-700 flex items-center">
                <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
                After Optimization
              </h3>
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Profile:</span>
                    <span className="font-medium">{beforeAfterComparison.after?.profile?.name || 'Default'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Voice:</span>
                    <span className="font-medium">{beforeAfterComparison.after?.config_snapshot?.voice_settings?.voice_id || 'default'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Updated:</span>
                    <span className="font-medium">{new Date(beforeAfterComparison.after?.timestamp).toLocaleTimeString()}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Changes Summary */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="text-sm font-medium text-blue-900 mb-2">Changes Made:</h4>
            <ul className="space-y-1 text-sm text-blue-800">
              {beforeAfterComparison.changes_summary?.map((change, index) => (
                <li key={index} className="flex items-center">
                  <CheckCircle className="w-4 h-4 mr-2 text-blue-600" />
                  {change}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
};

export default Optimization;