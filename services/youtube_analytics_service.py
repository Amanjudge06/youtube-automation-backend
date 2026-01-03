"""
YouTube Analytics Service
Pulls detailed performance data from YouTube channels and videos for optimization
"""

import logging
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from pathlib import Path
import config
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import statistics

logger = logging.getLogger(__name__)

class YouTubeAnalyticsService:
    """Analyze YouTube channel and video performance for content optimization"""
    
    def __init__(self):
        self.api_key = config.YOUTUBE_CLIENT_SECRET  # Will use OAuth for analytics
        self.channel_id = None
        self.analytics = None
        self.youtube = None
        self._setup_api_client()
    
    def _setup_api_client(self):
        """Setup YouTube Analytics API client"""
        try:
            # Use the same credentials as upload service for consistency
            from services.youtube_upload_service import YouTubeUploadService
            upload_service = YouTubeUploadService()
            
            # Try to get authenticated service
            if upload_service.authenticate():
                self.youtube = upload_service.youtube_service
                logger.info("YouTube Analytics API client initialized with authenticated service")
            else:
                # Fallback to basic API key (limited functionality)
                self.youtube = build('youtube', 'v3', developerKey=config.YOUTUBE_CLIENT_SECRET)
                logger.warning("Using basic API key - limited analytics functionality")
                
        except Exception as e:
            logger.error(f"Failed to setup YouTube API client: {e}")
    
    def set_channel_id(self, channel_id: str):
        """Set the channel ID to analyze"""
        self.channel_id = channel_id
        logger.info(f"Set analysis target channel: {channel_id}")
    
    def get_channel_performance(self, days: int = 30) -> Dict:
        """
        Get comprehensive channel performance metrics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with channel performance data
        """
        try:
            if not self.channel_id:
                logger.warning("No channel ID set for analysis")
                return {}
            
            logger.info(f"Analyzing channel performance for last {days} days...")
            
            # Get channel videos
            videos = self._get_recent_videos(days)
            
            if not videos:
                logger.warning("No recent videos found for analysis")
                return {}
            
            # Analyze video performance
            performance_data = {
                "total_videos": len(videos),
                "date_range": f"Last {days} days",
                "analysis_timestamp": datetime.now().isoformat(),
                "videos": [],
                "overall_metrics": {},
                "content_insights": {},
                "optimization_recommendations": {}
            }
            
            total_views = 0
            total_likes = 0
            total_comments = 0
            engagement_rates = []
            durations = []
            titles_analysis = []
            
            for video in videos:
                video_stats = self._get_video_detailed_stats(video['id'])
                
                if video_stats:
                    # Calculate engagement rate
                    views = int(video_stats.get('viewCount', 0))
                    likes = int(video_stats.get('likeCount', 0))
                    comments = int(video_stats.get('commentCount', 0))
                    
                    engagement_rate = ((likes + comments) / max(views, 1)) * 100
                    
                    video_data = {
                        "id": video['id'],
                        "title": video['title'],
                        "published_at": video['publishedAt'],
                        "duration": video.get('duration', 'Unknown'),
                        "views": views,
                        "likes": likes,
                        "comments": comments,
                        "engagement_rate": round(engagement_rate, 2),
                        "performance_score": self._calculate_performance_score(video_stats)
                    }
                    
                    performance_data["videos"].append(video_data)
                    
                    # Accumulate metrics
                    total_views += views
                    total_likes += likes
                    total_comments += comments
                    engagement_rates.append(engagement_rate)
                    titles_analysis.append(video['title'])
                    
                    # Parse duration if available
                    duration_seconds = self._parse_duration(video.get('duration', ''))
                    if duration_seconds:
                        durations.append(duration_seconds)
            
            # Calculate overall metrics
            performance_data["overall_metrics"] = {
                "total_views": total_views,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "average_views": round(total_views / len(videos)) if videos else 0,
                "average_engagement_rate": round(statistics.mean(engagement_rates), 2) if engagement_rates else 0,
                "average_duration": round(statistics.mean(durations)) if durations else 60,
                "best_performing_video": max(performance_data["videos"], key=lambda x: x['performance_score']) if performance_data["videos"] else None,
                "worst_performing_video": min(performance_data["videos"], key=lambda x: x['performance_score']) if performance_data["videos"] else None
            }
            
            # Generate content insights
            performance_data["content_insights"] = self._analyze_content_patterns(titles_analysis, performance_data["videos"])
            
            # Generate optimization recommendations
            performance_data["optimization_recommendations"] = self._generate_optimization_recommendations(performance_data)
            
            logger.info(f"Channel analysis complete: {len(videos)} videos analyzed")
            return performance_data
            
        except Exception as e:
            logger.error(f"Error analyzing channel performance: {e}")
            return {}
    
    def _get_recent_videos(self, days: int = 30) -> List[Dict]:
        """Get recent videos from the channel"""
        try:
            if not self.youtube or not self.channel_id:
                return []
            
            # Get uploads playlist ID
            channel_response = self.youtube.channels().list(
                part='contentDetails',
                id=self.channel_id
            ).execute()
            
            if not channel_response['items']:
                return []
            
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get recent videos from uploads playlist
            videos_response = self.youtube.playlistItems().list(
                part='snippet,contentDetails',
                playlistId=uploads_playlist_id,
                maxResults=50  # Adjust based on needs
            ).execute()
            
            videos = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for item in videos_response.get('items', []):
                published_at = datetime.fromisoformat(
                    item['snippet']['publishedAt'].replace('Z', '+00:00')
                )
                
                if published_at >= cutoff_date:
                    videos.append({
                        'id': item['contentDetails']['videoId'],
                        'title': item['snippet']['title'],
                        'publishedAt': item['snippet']['publishedAt'],
                        'description': item['snippet']['description'],
                        'thumbnail': item['snippet']['thumbnails'].get('medium', {}).get('url', '')
                    })
            
            logger.info(f"Found {len(videos)} recent videos for analysis")
            return videos
            
        except Exception as e:
            logger.error(f"Error getting recent videos: {e}")
            return []
    
    def _get_video_detailed_stats(self, video_id: str) -> Dict:
        """Get recent videos from the channel"""
        try:
            # Calculate date threshold
            date_threshold = datetime.now() - timedelta(days=days)
            
            # Search for recent videos
            request = self.youtube.search().list(
                part="snippet",
                channelId=self.channel_id,
                maxResults=50,
                order="date",
                publishedAfter=date_threshold.isoformat() + "Z",
                type="video"
            )
            
            response = request.execute()
            
            videos = []
            for item in response.get('items', []):
                video_data = {
                    "id": item['id']['videoId'],
                    "title": item['snippet']['title'],
                    "publishedAt": item['snippet']['publishedAt'],
                    "description": item['snippet']['description']
                }
                
                # Get additional video details
                video_details = self._get_video_details(video_data["id"])
                video_data.update(video_details)
                
                videos.append(video_data)
            
            return videos
            
        except Exception as e:
            logger.error(f"Error fetching recent videos: {e}")
            return []
    
    def _get_video_details(self, video_id: str) -> Dict:
        """Get detailed information about a specific video"""
        try:
            request = self.youtube.videos().list(
                part="contentDetails,statistics,snippet",
                id=video_id
            )
            
            response = request.execute()
            
            if response.get('items'):
                item = response['items'][0]
                return {
                    "duration": item['contentDetails']['duration'],
                    "statistics": item.get('statistics', {}),
                    "tags": item['snippet'].get('tags', [])
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching video details for {video_id}: {e}")
            return {}
    
    def _get_video_detailed_stats(self, video_id: str) -> Dict:
        """Get detailed statistics for a video"""
        try:
            request = self.youtube.videos().list(
                part="statistics",
                id=video_id
            )
            
            response = request.execute()
            
            if response.get('items'):
                return response['items'][0].get('statistics', {})
            
            return {}
            
        except Exception as e:
            logger.error(f"Error fetching video stats for {video_id}: {e}")
            return {}
    
    def _calculate_performance_score(self, stats: Dict) -> float:
        """Calculate a performance score for a video (0-100)"""
        try:
            views = int(stats.get('viewCount', 0))
            likes = int(stats.get('likeCount', 0))
            comments = int(stats.get('commentCount', 0))
            
            # Weighted performance score
            # Views contribute 50%, engagement (likes + comments) contributes 50%
            if views == 0:
                return 0
            
            engagement_score = ((likes + comments) / views) * 100
            view_score = min(views / 1000, 50)  # Cap views at 50K for scoring
            
            total_score = (view_score * 0.5) + (min(engagement_score, 50) * 0.5)
            
            return min(round(total_score, 1), 100.0)
            
        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0.0
    
    def _parse_duration(self, duration_str: str) -> Optional[int]:
        """Parse ISO 8601 duration to seconds"""
        try:
            # Simple parser for PT1M30S format
            if not duration_str.startswith('PT'):
                return None
            
            duration_str = duration_str[2:]  # Remove 'PT'
            
            minutes = 0
            seconds = 0
            
            if 'M' in duration_str:
                parts = duration_str.split('M')
                minutes = int(parts[0])
                duration_str = parts[1]
            
            if 'S' in duration_str:
                seconds = int(duration_str.replace('S', ''))
            
            return minutes * 60 + seconds
            
        except Exception as e:
            logger.error(f"Error parsing duration {duration_str}: {e}")
            return None
    
    def _analyze_content_patterns(self, titles: List[str], videos: List[Dict]) -> Dict:
        """Analyze content patterns from successful videos"""
        try:
            insights = {
                "title_patterns": {},
                "optimal_length": {},
                "engagement_factors": {},
                "timing_patterns": {}
            }
            
            # Analyze titles
            high_performing_titles = [v['title'] for v in videos if v['performance_score'] > 50]
            low_performing_titles = [v['title'] for v in videos if v['performance_score'] < 25]
            
            # Common words in high-performing titles
            high_words = ' '.join(high_performing_titles).lower().split()
            low_words = ' '.join(low_performing_titles).lower().split()
            
            # Find words that appear more in high-performing titles
            high_word_freq = {}
            for word in high_words:
                if len(word) > 3:  # Only consider meaningful words
                    high_word_freq[word] = high_word_freq.get(word, 0) + 1
            
            insights["title_patterns"] = {
                "effective_keywords": sorted(high_word_freq.items(), key=lambda x: x[1], reverse=True)[:10],
                "average_title_length": round(statistics.mean([len(title) for title in titles])) if titles else 0,
                "high_performing_titles": high_performing_titles[:5]
            }
            
            # Analyze optimal video length
            duration_performance = [(v.get('duration', 60), v['performance_score']) for v in videos if 'duration' in v]
            if duration_performance:
                optimal_durations = [dp[0] for dp in duration_performance if dp[1] > 50]
                if optimal_durations:
                    insights["optimal_length"] = {
                        "average_optimal_duration": round(statistics.mean(optimal_durations)),
                        "duration_range": f"{min(optimal_durations)}-{max(optimal_durations)} seconds"
                    }
            
            return insights
            
        except Exception as e:
            logger.error(f"Error analyzing content patterns: {e}")
            return {}
    
    def _generate_optimization_recommendations(self, performance_data: Dict) -> Dict:
        """Generate actionable optimization recommendations"""
        try:
            recommendations = {
                "script_optimization": [],
                "voiceover_optimization": [],
                "content_strategy": [],
                "timing_optimization": []
            }
            
            overall_metrics = performance_data.get("overall_metrics", {})
            content_insights = performance_data.get("content_insights", {})
            
            # Script optimization recommendations
            avg_engagement = overall_metrics.get("average_engagement_rate", 0)
            
            if avg_engagement < 2:
                recommendations["script_optimization"].append({
                    "issue": "Low engagement rate",
                    "recommendation": "Use more question-based hooks and call-to-action phrases",
                    "priority": "high",
                    "implementation": "Add 'What do you think?' and 'Let me know in comments' to scripts"
                })
            
            if avg_engagement < 1:
                recommendations["script_optimization"].append({
                    "issue": "Very low engagement",
                    "recommendation": "Include controversial or debate-worthy statements",
                    "priority": "high", 
                    "implementation": "Add opinion-based content that encourages discussion"
                })
            
            # Voiceover optimization
            best_video = overall_metrics.get("best_performing_video")
            if best_video:
                recommendations["voiceover_optimization"].append({
                    "issue": "Optimize voice style",
                    "recommendation": f"Analyze successful video '{best_video['title']}' for voice patterns",
                    "priority": "medium",
                    "implementation": "Match energy level and pace of top-performing content"
                })
            
            # Content strategy
            title_patterns = content_insights.get("title_patterns", {})
            effective_keywords = title_patterns.get("effective_keywords", [])
            
            if effective_keywords:
                top_keywords = [kw[0] for kw in effective_keywords[:5]]
                recommendations["content_strategy"].append({
                    "issue": "Keyword optimization",
                    "recommendation": f"Focus on high-performing keywords: {', '.join(top_keywords)}",
                    "priority": "high",
                    "implementation": "Incorporate these keywords into trending topic selection"
                })
            
            # Duration optimization
            avg_duration = overall_metrics.get("average_duration", 60)
            optimal_length = content_insights.get("optimal_length", {})
            
            if optimal_length and "average_optimal_duration" in optimal_length:
                optimal_dur = optimal_length["average_optimal_duration"]
                if abs(avg_duration - optimal_dur) > 10:
                    recommendations["content_strategy"].append({
                        "issue": "Video length optimization",
                        "recommendation": f"Target video length of {optimal_dur} seconds for better performance",
                        "priority": "medium",
                        "implementation": "Adjust script length to match optimal duration"
                    })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")
            return {}
    
    def save_analysis(self, performance_data: Dict, filepath: str = None):
        """Save analysis data for future reference"""
        try:
            if not filepath:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = f"logs/channel_analysis_{timestamp}.json"
            
            Path(filepath).parent.mkdir(exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(performance_data, f, indent=2, default=str)
            
            logger.info(f"Channel analysis saved to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")
            return None
    
    def get_optimization_insights(self) -> Dict:
        """Get quick optimization insights for immediate use"""
        try:
            performance_data = self.get_channel_performance(days=14)  # Last 2 weeks
            
            if not performance_data:
                return {"status": "no_data", "message": "No channel data available for analysis"}
            
            recommendations = performance_data.get("optimization_recommendations", {})
            content_insights = performance_data.get("content_insights", {})
            
            # Extract actionable insights
            insights = {
                "status": "success",
                "script_adjustments": [],
                "voiceover_adjustments": [],
                "content_focus": [],
                "performance_summary": performance_data.get("overall_metrics", {})
            }
            
            # Extract script adjustments
            for rec in recommendations.get("script_optimization", []):
                if rec.get("priority") == "high":
                    insights["script_adjustments"].append({
                        "adjustment": rec["recommendation"],
                        "reason": rec["issue"]
                    })
            
            # Extract voiceover adjustments
            for rec in recommendations.get("voiceover_optimization", []):
                insights["voiceover_adjustments"].append({
                    "adjustment": rec["recommendation"],
                    "reason": rec["issue"]
                })
            
            # Extract content focus areas
            title_patterns = content_insights.get("title_patterns", {})
            if title_patterns.get("effective_keywords"):
                keywords = [kw[0] for kw in title_patterns["effective_keywords"][:3]]
                insights["content_focus"] = keywords
            
            return insights
            
        except Exception as e:
            logger.error(f"Error getting optimization insights: {e}")
            return {"status": "error", "message": str(e)}