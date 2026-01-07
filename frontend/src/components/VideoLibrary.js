import React, { useState, useEffect } from 'react';
import { 
  Video, 
  Download, 
  Eye, 
  Clock, 
  Calendar,
  Youtube,
  ExternalLink,
  Filter,
  Search
} from 'lucide-react';

const API_BASE = process.env.REACT_APP_API_URL || '';

const VideoLibrary = () => {
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterBy, setFilterBy] = useState('all');
  const [selectedVideo, setSelectedVideo] = useState(null);

  useEffect(() => {
    fetchVideos();
  }, []);

  const fetchVideos = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/videos`);
      if (!response.ok) throw new Error('Failed to fetch videos');
      const data = await response.json();
      setVideos(data.videos || []);
    } catch (error) {
      console.error('Error fetching videos:', error);
      alert('Failed to fetch videos: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const filteredVideos = videos.filter(video => {
    const matchesSearch = video.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         video.topic.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesFilter = filterBy === 'all' || 
                         (filterBy === 'uploaded' && video.youtube_url) ||
                         (filterBy === 'local' && !video.youtube_url);
    
    return matchesSearch && matchesFilter;
  });

  const VideoCard = ({ video }) => (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
      {/* Video Thumbnail/Preview */}
      <div className="aspect-video bg-gray-100 flex items-center justify-center">
        <Video className="w-12 h-12 text-gray-400" />
      </div>
      
      {/* Video Info */}
      <div className="p-4">
        <h3 className="font-semibold text-gray-900 text-sm mb-2 line-clamp-2">
          {video.title}
        </h3>
        
        <div className="space-y-2 text-xs text-gray-500">
          <div className="flex items-center">
            <Calendar className="w-3 h-3 mr-1" />
            {new Date(video.created_at).toLocaleDateString()}
          </div>
          <div className="flex items-center">
            <Clock className="w-3 h-3 mr-1" />
            {Math.round(video.duration)}s
          </div>
          <div className="flex items-center">
            <span className="inline-block w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
            {video.topic}
          </div>
        </div>
        
        {/* Performance Metrics */}
        <div className="mt-3 pt-3 border-t border-gray-100">
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-gray-500">Images:</span>
              <span className="ml-1 font-medium">{video.performance.images_used}</span>
            </div>
            <div>
              <span className="text-gray-500">Scenes:</span>
              <span className="ml-1 font-medium">{video.performance.scenes}</span>
            </div>
          </div>
        </div>
        
        {/* Action Buttons */}
        <div className="mt-4 flex items-center justify-between">
          <div className="flex space-x-2">
            <button
              onClick={() => setSelectedVideo(video)}
              className="flex items-center px-2 py-1 text-blue-600 hover:bg-blue-50 rounded text-xs"
            >
              <Eye className="w-3 h-3 mr-1" />
              View
            </button>
            <a
              href={`/api/videos/${video.id}/download`}
              className="flex items-center px-2 py-1 text-gray-600 hover:bg-gray-50 rounded text-xs"
            >
              <Download className="w-3 h-3 mr-1" />
              Download
            </a>
          </div>
          
          {video.youtube_url && (
            <a
              href={video.youtube_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center px-2 py-1 text-red-600 hover:bg-red-50 rounded text-xs"
            >
              <Youtube className="w-3 h-3 mr-1" />
              YouTube
            </a>
          )}
        </div>
      </div>
    </div>
  );

  const VideoModal = ({ video, onClose }) => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl max-h-[90vh] w-full overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-start mb-4">
            <h2 className="text-xl font-bold text-gray-900">{video.title}</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <span className="sr-only">Close</span>
              ✕
            </button>
          </div>
          
          {/* Video Preview */}
          <div className="aspect-video bg-gray-100 rounded-lg mb-6 flex items-center justify-center">
            <Video className="w-20 h-20 text-gray-400" />
            <p className="ml-4 text-gray-600">Video Player Placeholder</p>
          </div>
          
          {/* Video Details */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Details</h3>
              <dl className="space-y-2 text-sm">
                <div>
                  <dt className="text-gray-500">Topic:</dt>
                  <dd className="font-medium">{video.topic}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Duration:</dt>
                  <dd className="font-medium">{Math.round(video.duration)}s</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Created:</dt>
                  <dd className="font-medium">{new Date(video.created_at).toLocaleString()}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">File:</dt>
                  <dd className="font-medium text-xs text-gray-600">{video.id}.mp4</dd>
                </div>
              </dl>
            </div>
            
            <div>
              <h3 className="font-semibold text-gray-900 mb-3">Performance</h3>
              <dl className="space-y-2 text-sm">
                <div>
                  <dt className="text-gray-500">Images Used:</dt>
                  <dd className="font-medium">{video.performance.images_used}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Scenes:</dt>
                  <dd className="font-medium">{video.performance.scenes}</dd>
                </div>
                <div>
                  <dt className="text-gray-500">Script Length:</dt>
                  <dd className="font-medium">{video.performance.script_length} chars</dd>
                </div>
                {video.youtube_url && (
                  <div>
                    <dt className="text-gray-500">YouTube:</dt>
                    <dd>
                      <a
                        href={video.youtube_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center text-red-600 hover:text-red-800"
                      >
                        <ExternalLink className="w-3 h-3 mr-1" />
                        View on YouTube
                      </a>
                    </dd>
                  </div>
                )}
              </dl>
            </div>
          </div>
          
          {/* Actions */}
          <div className="mt-6 flex justify-end space-x-3">
            <a
              href={`/api/videos/${video.id}/download`}
              className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
            >
              <Download className="w-4 h-4 mr-2" />
              Download
            </a>
            {video.youtube_url && (
              <a
                href={video.youtube_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
              >
                <Youtube className="w-4 h-4 mr-2" />
                YouTube
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Video Library</h1>
        <p className="text-gray-600">Browse and manage your generated videos</p>
      </div>

      {/* Filters and Search */}
      <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search videos..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
          
          {/* Filter */}
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={filterBy}
              onChange={(e) => setFilterBy(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm"
            >
              <option value="all">All Videos</option>
              <option value="uploaded">Uploaded to YouTube</option>
              <option value="local">Local Only</option>
            </select>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="text-2xl font-bold text-blue-600">{videos.length}</div>
          <div className="text-sm text-gray-500">Total Videos</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="text-2xl font-bold text-green-600">
            {videos.filter(v => v.youtube_url).length}
          </div>
          <div className="text-sm text-gray-500">Uploaded to YouTube</div>
        </div>
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <div className="text-2xl font-bold text-purple-600">
            {Math.round(videos.reduce((acc, v) => acc + v.duration, 0) / 60)}m
          </div>
          <div className="text-sm text-gray-500">Total Duration</div>
        </div>
      </div>

      {/* Videos Grid */}
      {loading ? (
        <div className="flex justify-center items-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      ) : filteredVideos.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredVideos.map((video) => (
            <VideoCard key={video.id} video={video} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <Video className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No videos found</h3>
          <p className="mt-1 text-sm text-gray-500">
            {searchTerm || filterBy !== 'all' 
              ? 'Try adjusting your search or filter.' 
              : 'Start by generating your first video.'}
          </p>
        </div>
      )}

      {/* Video Detail Modal */}
      {selectedVideo && (
        <VideoModal
          video={selectedVideo}
          onClose={() => setSelectedVideo(null)}
        />
      )}
    </div>
  );
};

export default VideoLibrary;