"""
YouTube Upload Service
Handles video uploads to YouTube with SEO optimization and metadata management
"""

import logging
import json
import os
import pickle
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
import secrets

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import requests
from PIL import Image

import config

logger = logging.getLogger(__name__)


class YouTubeUploadService:
    """Service for uploading videos to YouTube with SEO optimization"""
    
    def __init__(self):
        self.youtube_service = None
        self.credentials_file = config.BASE_DIR / "youtube_credentials.json"
        self.token_file = config.BASE_DIR / "youtube_token.pickle"
        self.scopes = ['https://www.googleapis.com/auth/youtube.upload', 
                      'https://www.googleapis.com/auth/youtube.readonly']
    
    def _get_client_config(self):
        """Get client configuration from file or environment variables"""
        # Try loading from file first
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load credentials file: {e}")
        
        # Fallback to environment variables
        if config.YOUTUBE_CLIENT_ID and config.YOUTUBE_CLIENT_SECRET:
            logger.info("Using YouTube credentials from environment variables")
            return {
                "web": {
                    "client_id": config.YOUTUBE_CLIENT_ID,
                    "client_secret": config.YOUTUBE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "redirect_uris": [config.YOUTUBE_REDIRECT_URI]
                }
            }
            
        raise Exception("YouTube credentials not found. Please ensure youtube_credentials.json exists or YOUTUBE_CLIENT_ID/SECRET env vars are set.")

    def get_auth_url(self):
        """Generate YouTube OAuth URL for new channel authentication"""
        try:
            client_config = self._get_client_config()
            
            # Create OAuth flow
            flow = InstalledAppFlow.from_client_config(
                client_config, 
                scopes=self.scopes
            )
            
            # Generate authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true'
            )
            
            # Store flow state for later use
            self.temp_flow = flow
            
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating auth URL: {e}")
            raise
    
    def get_auth_url_for_user(self, user_id: str):
        """Generate YouTube OAuth URL for a specific user"""
        try:
            client_config = self._get_client_config()
            
            # For SaaS, we need to use the web flow, not installed app flow
            # Extract client ID from config (could be 'web' or 'installed')
            app_type = list(client_config.keys())[0]
            client_id = client_config[app_type]['client_id']
            
            # Build OAuth URL manually for web application flow
            from urllib.parse import urlencode
            import config
            
            base_url = "https://accounts.google.com/o/oauth2/auth"
            params = {
                'client_id': client_id,
                'redirect_uri': config.YOUTUBE_REDIRECT_URI,
                'scope': ' '.join(self.scopes),
                'response_type': 'code',
                'access_type': 'offline',
                'include_granted_scopes': 'true',
                'state': user_id,
                'prompt': 'consent'  # Force consent screen to get refresh token
            }
            
            auth_url = f"{base_url}?{urlencode(params)}"
            
            logger.info(f"Generated OAuth URL for user {user_id}")
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating auth URL for user {user_id}: {e}")
            raise
    
    def authenticate_user_with_code(self, user_id: str, auth_code: str):
        """Authenticate user with provided authorization code"""
        try:
            from services.user_manager import user_manager
            import requests
            import config
            
            # Exchange authorization code for tokens using web flow
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                'client_id': config.YOUTUBE_CLIENT_ID,
                'client_secret': config.YOUTUBE_CLIENT_SECRET,
                'code': auth_code,
                'grant_type': 'authorization_code',
                'redirect_uri': config.YOUTUBE_REDIRECT_URI
            }
            
            # Exchange code for tokens
            response = requests.post(token_url, data=token_data)
            if response.status_code != 200:
                logger.error(f"Token exchange failed: {response.text}")
                return False, None
            
            token_info = response.json()
            
            # Create credentials object
            from google.oauth2.credentials import Credentials
            creds = Credentials(
                token=token_info['access_token'],
                refresh_token=token_info.get('refresh_token'),
                id_token=token_info.get('id_token'),
                token_uri='https://oauth2.googleapis.com/token',
                client_id=config.YOUTUBE_CLIENT_ID,
                client_secret=config.YOUTUBE_CLIENT_SECRET,
                scopes=self.scopes
            )
            
            # Build YouTube service to get channel info
            youtube_service = build('youtube', 'v3', credentials=creds)
            
            # Get channel information
            request = youtube_service.channels().list(
                part='id,snippet,statistics',
                mine=True
            )
            response = request.execute()
            
            if response['items']:
                channel = response['items'][0]
                channel_info = {
                    "id": channel['id'],
                    "title": channel['snippet']['title'],
                    "subscriber_count": int(channel['statistics'].get('subscriberCount', 0)),
                    "view_count": int(channel['statistics'].get('viewCount', 0)),
                    "video_count": int(channel['statistics'].get('videoCount', 0))
                }
                
                # Store credentials and channel info for user
                success = user_manager.add_youtube_channel(user_id, channel_info, creds)
                
                if success:
                    logger.info(f"Successfully authenticated user {user_id} with channel {channel_info['title']}")
                    return True, channel_info
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error authenticating user {user_id} with code: {e}")
            return False, None
    
    def authenticate_with_code(self, auth_code: str):
        """Legacy method - authenticate with provided authorization code"""
        try:
            if not hasattr(self, 'temp_flow'):
                # Recreate flow if needed
                client_config = self._get_client_config()
                flow = InstalledAppFlow.from_client_config(
                    client_config, 
                    scopes=self.scopes
                )
            else:
                flow = self.temp_flow
            
            # Exchange authorization code for credentials
            flow.fetch_token(code=auth_code)
            creds = flow.credentials
            
            # Save credentials
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
            
            # Build YouTube service
            self.youtube_service = build('youtube', 'v3', credentials=creds)
            
            logger.info("Successfully authenticated with YouTube API")
            return True
            
        except Exception as e:
            logger.error(f"Error authenticating with code: {e}")
            return False
    
    def authenticate(self):
        """Authenticate with YouTube API using OAuth 2.0"""
        creds = None
        
        # Load existing token
        if self.token_file.exists():
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no valid credentials, get new ones
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing YouTube API credentials...")
                creds.refresh(Request())
            else:
                logger.info("Starting YouTube API authentication flow...")
                
                # Check if we have client credentials
                if not config.YOUTUBE_CLIENT_ID or not config.YOUTUBE_CLIENT_SECRET:
                    logger.error("YouTube Client ID and Secret not configured")
                    logger.info("Please set up YouTube API credentials:")
                    logger.info("1. Go to https://console.cloud.google.com/")
                    logger.info("2. Create a new project or select existing")
                    logger.info("3. Enable YouTube Data API v3")
                    logger.info("4. Create OAuth 2.0 credentials")
                    logger.info("5. Set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET in config.py")
                    return False
                
                # Create credentials JSON
                client_config = {
                    "web": {
                        "client_id": config.YOUTUBE_CLIENT_ID,
                        "client_secret": config.YOUTUBE_CLIENT_SECRET,
                        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                        "token_uri": "https://oauth2.googleapis.com/token",
                        "redirect_uris": [config.YOUTUBE_REDIRECT_URI]
                    }
                }
                
                flow = InstalledAppFlow.from_client_config(
                    client_config, config.YOUTUBE_UPLOAD_SCOPES
                )
                creds = flow.run_local_server(port=8080)
            
            # Save credentials for next time
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)
        
        # Build the service
        self.youtube_service = build('youtube', 'v3', credentials=creds)
        logger.info("✅ YouTube API authenticated successfully")
        
        # Get and store channel information
        self._get_my_channel_info()
        return True
    
    def _get_my_channel_info(self):
        """Get authenticated user's channel information and store it"""
        try:
            # Get my channel info
            request = self.youtube_service.channels().list(
                part='id,snippet,statistics',
                mine=True
            )
            response = request.execute()
            
            if response.get('items'):
                channel = response['items'][0]
                channel_info = {
                    'channel_id': channel['id'],
                    'channel_title': channel['snippet']['title'],
                    'channel_url': f"https://www.youtube.com/channel/{channel['id']}",
                    'custom_url': channel['snippet'].get('customUrl', ''),
                    'subscriber_count': int(channel['statistics'].get('subscriberCount', 0)),
                    'video_count': int(channel['statistics'].get('videoCount', 0)),
                    'view_count': int(channel['statistics'].get('viewCount', 0))
                }
                
                # Store channel info in config file
                channel_file = config.BASE_DIR / "my_channel_info.json"
                with open(channel_file, 'w') as f:
                    json.dump(channel_info, f, indent=2)
                
                logger.info(f"✅ Channel info stored: {channel_info['channel_title']} ({channel_info['channel_id']})")
                return channel_info
            else:
                logger.warning("No channel found for authenticated user")
                return None
                
        except Exception as e:
            logger.error(f"Failed to get channel info: {e}")
            return None
    
    def get_my_channel_info(self) -> Optional[Dict]:
        """Get stored channel information"""
        try:
            channel_file = config.BASE_DIR / "my_channel_info.json"
            if channel_file.exists():
                with open(channel_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read channel info: {e}")
        return None
    
    def optimize_metadata_for_seo(self, metadata: Dict, research_data: Dict = None) -> Dict:
        """
        Optimize video metadata for YouTube SEO
        
        Args:
            metadata: Original metadata from video generation
            research_data: Optional research data for enhanced SEO
            
        Returns:
            Optimized metadata dictionary
        """
        optimized = metadata.copy()
        
        # Optimize title
        title = metadata.get('title', '')
        optimized_title = self._optimize_title(title, metadata.get('topic', ''))
        optimized['optimized_title'] = optimized_title
        
        # Optimize description
        description = self._create_seo_description(metadata, research_data)
        optimized['optimized_description'] = description
        
        # Generate SEO tags
        tags = self._generate_seo_tags(metadata, research_data)
        optimized['optimized_tags'] = tags
        
        # Generate trending hashtags
        hashtags = self._generate_trending_hashtags(metadata, research_data)
        optimized['trending_hashtags'] = hashtags
        
        return optimized
    
    def _optimize_title(self, title: str, topic: str) -> str:
        """Optimize video title to be engaging, humanized, and topic-specific"""
        
        # If we have a proper title from script generation, use it with minimal optimization
        if title and title != f'Breaking: {topic}' and len(title) > 10:
            # This is a real generated title, just clean it up
            cleaned_title = re.sub(r'[!]{3,}', '!!', title)
            cleaned_title = re.sub(r'[?]{3,}', '??', cleaned_title)
            
            # Ensure proper length
            max_length = config.YOUTUBE_SEO_CONFIG["max_title_length"]
            if len(cleaned_title) > max_length:
                cleaned_title = cleaned_title[:max_length-3] + "..."
                
            return cleaned_title
        
        # If no proper title, generate a humanized one from topic
        topic_clean = topic.replace('_', ' ').replace('-', ' ').title()
        
        # Create engaging, humanized titles based on topic type
        if 'vs' in topic.lower() and any(sport in topic.lower() for sport in ['football', 'game', 'bowl']):
            # Sports game
            return f"You Won't Believe What Happened in {topic_clean}!"
        elif 'breaking' in topic.lower():
            # Breaking news
            return f"{topic_clean}: Here's What We Know"
        elif any(celeb in topic.lower() for celeb in ['taylor swift', 'elon musk', 'celebrity']):
            # Celebrity news
            return f"{topic_clean} - The Internet Can't Stop Talking About This"
        elif 'earthquake' in topic.lower():
            # Natural disaster
            return f"🚨 {topic_clean}: What You Need to Know Right Now"
        else:
            # General trending topic
            return f"{topic_clean} - Why Everyone's Talking About This"
        
        # Fallback: clean up the topic
        return topic_clean
    
    def _create_seo_description(self, metadata: Dict, research_data: Dict = None) -> str:
        """Create comprehensive SEO-optimized description using full 5000 character limit"""
        
        topic = metadata.get('topic', '')
        title = metadata.get('optimized_title', metadata.get('title', ''))
        script = metadata.get('script', '')
        trend_breakdown = metadata.get('trend_breakdown', [])
        
        description_parts = []
        
        # 1. Natural, humanized hook (100-150 chars)
        if 'vs' in topic.lower() and any(sport in topic.lower() for sport in ['football', 'game', 'bowl']):
            # Sports content
            hook = f"This {topic} game had moments that left everyone speechless. Here's what went down and why it's got the sports world buzzing!"
        elif 'earthquake' in topic.lower():
            # Natural disaster  
            hook = f"Major developments in the {topic} situation. Here's the latest information and what it means for everyone affected."
        elif 'celebrity' in topic.lower() or any(name in topic.lower() for name in ['taylor swift', 'elon musk', 'kim kardashian']):
            # Celebrity news
            hook = f"The latest on {title} has everyone talking. Here's what happened and why it's trending everywhere."
        elif 'technology' in topic.lower() or 'ai' in topic.lower():
            # Tech news
            hook = f"This {topic} development could change everything. Here's what you need to know about this breakthrough."
        else:
            # General trending
            hook = f"Everyone's talking about {title} right now. Here's the full story and why it matters."
        
        description_parts.append(hook)
        description_parts.append("")
        
        # 2. Comprehensive Summary (400-600 chars)
        if research_data and research_data.get('summary'):
            summary = research_data['summary']
            if len(summary) > 500:
                # Use first 500 chars and add continuation
                main_summary = summary[:500].rsplit(' ', 1)[0] + "..."
            else:
                main_summary = summary
            
            description_parts.append("📖 FULL STORY:")
            description_parts.append(main_summary)
            description_parts.append("")
        
        # 3. Detailed Key Points (800-1000 chars)
        if research_data:
            key_points = research_data.get('key_points', [])
            if key_points:
                description_parts.append("🎯 KEY DETAILS YOU NEED TO KNOW:")
                for i, point in enumerate(key_points[:8], 1):  # Use up to 8 key points
                    description_parts.append(f"   {i}. {point}")
                description_parts.append("")
        
        # 4. What People Are Searching For (300-500 chars)
        if trend_breakdown:
            description_parts.append("🔍 WHAT PEOPLE ARE ASKING:")
            # Use trend breakdown queries to show what people want to know
            for i, query in enumerate(trend_breakdown[:6], 1):  # Top 6 related searches
                description_parts.append(f"   • {query}")
            description_parts.append("")
        
        # 5. Impact & Context (200-400 chars)
        if research_data and research_data.get('location'):
            location = research_data['location']
            description_parts.append(f"🌍 GLOBAL IMPACT: This {topic} situation in {location} has implications worldwide.")
        else:
            description_parts.append(f"🌍 WHY THIS MATTERS: Understanding {topic} is crucial in today's rapidly changing world.")
        description_parts.append("")
        
        # 6. Timeline (if available) (200-300 chars)
        if research_data and research_data.get('timeline'):
            description_parts.append("⏱️ TIMELINE OF EVENTS:")
            timeline = research_data['timeline'][:200] if len(research_data['timeline']) > 200 else research_data['timeline']
            description_parts.append(timeline)
            description_parts.append("")
        
        # 7. Scene-by-Scene Breakdown (300-500 chars)
        scenes = metadata.get('scenes', [])
        if len(scenes) > 1:
            description_parts.append("📺 VIDEO BREAKDOWN:")
            for scene in scenes:
                time_range = scene.get('time', 'Unknown')
                narration = scene.get('narration', '')[:50] + '...' if len(scene.get('narration', '')) > 50 else scene.get('narration', '')
                description_parts.append(f"   {time_range}: {narration}")
            description_parts.append("")
        
        # 8. Strong Call-to-Actions (200-300 chars)
        description_parts.extend([
            "🚀 TAKE ACTION NOW:",
            "👍 SMASH that LIKE button if this shocked you!",
            "🔔 SUBSCRIBE + Turn ON notifications for breaking news!",
            "💬 COMMENT your thoughts - What do you think will happen next?",
            "📤 SHARE this with someone who needs to know!",
            "🔄 Check our other videos for more breaking stories!",
            ""
        ])
        
        # 9. Topic Tags for Discoverability (200-400 chars)
        description_parts.append("🏷️ RELATED TOPICS:")
        tags_for_description = []
        if trend_breakdown:
            # Use trend breakdown as related topics
            for query in trend_breakdown[:10]:
                # Convert queries to hashtag format
                hashtag = '#' + ''.join(word.capitalize() for word in query.split()[:3])  # Max 3 words per hashtag
                if len(hashtag) < 30:  # Keep hashtags reasonable length
                    tags_for_description.append(hashtag)
        
        # Add strategic hashtags
        strategic_hashtags = [
            f"#{topic.replace(' ', '')}",
            "#BreakingNews",
            "#Trending",
            "#Viral",
            "#MustWatch",
            "#Shorts",
            "#FYP",
            "#YouTubeShorts",
            "#News2025"
        ]
        tags_for_description.extend(strategic_hashtags)
        
        # Limit hashtags to avoid spam
        final_hashtags = list(dict.fromkeys(tags_for_description))[:20]  # Remove duplicates, limit to 20
        description_parts.append(" ".join(final_hashtags))
        description_parts.append("")
        
        # 10. Channel Promotion (100-200 chars)
        description_parts.extend([
            "🎬 ABOUT OUR CHANNEL:",
            "We bring you the latest breaking news, trending topics, and viral stories from around the world. Stay informed, stay ahead!",
            "",
            "⚡ New videos daily | 📱 Follow trends | 🌐 Global coverage",
            ""
        ])
        
        # 11. Legal/Disclaimer (if needed) (100-150 chars)
        description_parts.extend([
            "📋 DISCLAIMER: All information is sourced from reliable news outlets and research. Views expressed are for informational purposes.",
            "",
            "© 2025 All Rights Reserved. Fair use applies."
        ])
        
        # Combine all parts
        full_description = "\n".join(description_parts)
        
        # Ensure we're close to but not over the 5000 character limit
        max_length = 4950  # Leave small buffer
        if len(full_description) > max_length:
            # Trim from the middle sections while keeping the most important parts
            essential_parts = [
                description_parts[0],  # Hook
                description_parts[1],  # Empty line
            ]
            
            # Add summary if available
            if research_data and research_data.get('summary'):
                essential_parts.extend(description_parts[2:5])  # Summary section
            
            # Always keep call-to-actions and hashtags
            essential_parts.extend(description_parts[-10:])  # Last 10 parts (CTAs, hashtags, etc.)
            
            full_description = "\n".join(essential_parts)
            
            # If still too long, truncate with warning
            if len(full_description) > max_length:
                full_description = full_description[:max_length-20] + "\n\n[Content truncated]"
        
        logger.info(f"Generated comprehensive description: {len(full_description)} characters")
        return full_description
    
    def _generate_seo_tags(self, metadata: Dict, research_data: Dict = None) -> List[str]:
        """Generate SEO-optimized tags specific to the video topic"""
        
        tags = []
        topic = metadata.get('topic', '').lower()
        
        # Priority 1: Topic-specific keywords (most important)
        topic_words = topic.replace(',', ' ').replace('-', ' ').split()
        for word in topic_words:
            word = word.strip()
            if len(word) > 2 and word not in ['vs', 'the', 'and', 'or', 'in', 'on', 'at', 'to', 'for', 'of']:
                tags.append(word)
        
        # Priority 2: Add contextual tags based on topic type
        if any(sport in topic for sport in ['football', 'vs', 'game', 'bowl', 'playoffs']):
            sport_tags = ['football', 'college football', 'sports', 'game highlights', 'sports news']
            tags.extend([tag for tag in sport_tags if tag not in tags])
        elif any(news in topic for news in ['breaking', 'news', 'update', 'announcement']):
            news_tags = ['breaking news', 'news update', 'current events', 'latest news']
            tags.extend([tag for tag in news_tags if tag not in tags])
        elif any(tech in topic for tech in ['ai', 'technology', 'tech', 'innovation']):
            tech_tags = ['technology', 'tech news', 'innovation', 'ai']
            tags.extend([tag for tag in tech_tags if tag not in tags])
        
        # Priority 3: Research-based specific keywords
        if research_data and research_data.get('key_points'):
            for point in research_data['key_points'][:3]:  # Top 3 key points
                words = point.lower().split()
                for word in words:
                    if len(word) > 4 and word.isalpha() and word not in tags:
                        if len(tags) < 20:  # Limit total tags
                            tags.append(word)
        
        # Priority 4: Add performance tags (keep these minimal and relevant)
        performance_tags = ['shorts', 'trending', 'viral']
        if 'breaking' in topic.lower():
            performance_tags.append('breaking')
        tags.extend([tag for tag in performance_tags if tag not in tags])
        
        # Clean and return top 15 tags
        unique_tags = list(dict.fromkeys(tags))[:15]
        logger.info(f"Generated {len(unique_tags)} topic-specific tags: {unique_tags[:5]}...")
        return unique_tags
        
        # Calculate character count and trim if needed
        tag_string = ', '.join(unique_tags)
        if len(tag_string) > 495:  # Leave 5 chars buffer
            # Trim tags to fit within character limit
            trimmed_tags = []
            char_count = 0
            for tag in unique_tags:
                if char_count + len(tag) + 2 <= 495:  # +2 for comma and space
                    trimmed_tags.append(tag)
                    char_count += len(tag) + 2
                else:
                    break
            unique_tags = trimmed_tags
        
        logger.info(f"Generated {len(unique_tags)} SEO tags ({len(', '.join(unique_tags))} characters)")
        return unique_tags[:50]  # YouTube recommends 5-15 tags, but we'll use more specific ones
    
    def _get_category_specific_tags(self, topic: str) -> List[str]:
        """Get high-performing tags based on topic category"""
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ['earthquake', 'disaster', 'emergency', 'breaking']):
            return ['earthquake', 'breaking news', 'disaster', 'safety', 'emergency response', 'natural disaster', 'seismic activity', 'emergency alert', 'disaster relief', 'earthquake safety']
        elif any(word in topic_lower for word in ['celebrity', 'actor', 'singer', 'star']):
            return ['celebrity news', 'entertainment', 'hollywood', 'celebrity gossip', 'star news', 'celebrity update', 'entertainment news', 'celebrity life', 'famous people', 'celebrity drama']
        elif any(word in topic_lower for word in ['technology', 'tech', 'ai', 'artificial intelligence']):
            return ['technology', 'tech news', 'innovation', 'artificial intelligence', 'tech review', 'gadgets', 'tech update', 'future tech', 'tech trends', 'tech breakthrough']
        elif any(word in topic_lower for word in ['politics', 'election', 'government']):
            return ['politics', 'political news', 'government', 'election', 'political update', 'policy', 'political analysis', 'current affairs', 'political events', 'government news']
        elif any(word in topic_lower for word in ['sports', 'football', 'basketball', 'soccer']):
            return ['sports news', 'sports update', 'athletic performance', 'sports highlights', 'game recap', 'sports analysis', 'athlete news', 'championship', 'tournament', 'sports drama']
        elif any(word in topic_lower for word in ['health', 'medical', 'doctor', 'medicine']):
            return ['health news', 'medical breakthrough', 'healthcare', 'wellness', 'medical research', 'health tips', 'medical update', 'health alert', 'medical advice', 'health information']
        else:
            return ['trending news', 'current events', 'latest news', 'breaking update', 'news alert', 'happening now', 'recent events', 'news update', 'current affairs', 'today news']
    
    def _get_strategic_trending_tags(self, topic: str, metadata: Dict) -> List[str]:
        """Get strategic trending tags that boost discoverability"""
        # Time-sensitive tags
        import datetime
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().strftime('%B').lower()
        
        strategic_tags = [
            f"{current_year}",
            f"{current_month} {current_year}",
            "trending now",
            "viral news",
            "breaking update",
            "must watch",
            "shocking news",
            "latest update",
            "today news",
            "current events"
        ]
        
        # Add engagement-driving tags
        strategic_tags.extend([
            "shorts",
            "viral shorts",
            "trending shorts",
            "news shorts",
            "breaking shorts",
            "fyp",
            "for you page",
            "youtube shorts"
        ])
        
        return strategic_tags
    
    def _generate_trending_hashtags(self, metadata: Dict, research_data: Dict = None) -> List[str]:
        """Generate trending hashtags"""
        
        hashtags = []
        topic = metadata.get('topic', '')
        
        # Convert topic to hashtag
        topic_hashtag = '#' + ''.join(word.capitalize() for word in topic.split())
        hashtags.append(topic_hashtag)
        
        # Add trending hashtags based on topic
        if 'earthquake' in topic.lower():
            hashtags.extend(['#BreakingNews', '#Earthquake', '#Safety', '#Emergency'])
        elif 'technology' in topic.lower():
            hashtags.extend(['#Tech', '#Innovation', '#TechNews'])
        
        # Add general trending hashtags
        hashtags.extend(['#Viral', '#Trending', '#Shorts', '#FYP'])
        
        return hashtags[:config.YOUTUBE_SEO_CONFIG["trending_hashtags_count"]]
    
    def create_thumbnail(self, video_path: Path, output_path: Path = None) -> Optional[Path]:
        """
        Create an optimized thumbnail from video
        
        Args:
            video_path: Path to the video file
            output_path: Optional custom output path
            
        Returns:
            Path to created thumbnail or None if failed
        """
        try:
            import cv2
            
            if output_path is None:
                output_path = video_path.parent / f"{video_path.stem}_thumbnail.jpg"
            
            # Capture frame from middle of video
            cap = cv2.VideoCapture(str(video_path))
            
            # Get total frames and go to middle
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            middle_frame = total_frames // 2
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, middle_frame)
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                # Resize to YouTube thumbnail dimensions
                height, width = frame.shape[:2]
                target_size = config.YOUTUBE_CONFIG["thumbnail_size"]
                
                # Calculate aspect ratio
                aspect = width / height
                target_aspect = target_size[0] / target_size[1]
                
                if aspect > target_aspect:
                    # Image is wider, crop width
                    new_width = int(height * target_aspect)
                    start_x = (width - new_width) // 2
                    frame = frame[:, start_x:start_x + new_width]
                else:
                    # Image is taller, crop height
                    new_height = int(width / target_aspect)
                    start_y = (height - new_height) // 2
                    frame = frame[start_y:start_y + new_height, :]
                
                # Resize to exact dimensions
                frame = cv2.resize(frame, target_size)
                
                # Save thumbnail
                cv2.imwrite(str(output_path), frame)
                logger.info(f"Thumbnail created: {output_path}")
                return output_path
            
        except ImportError:
            logger.warning("OpenCV not available for thumbnail generation")
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}")
        
        return None
    
    def upload_video(self, video_path: Path, metadata_path: Path, research_data: Dict = None) -> Dict:
        """
        Upload video to YouTube with optimized metadata
        
        Args:
            video_path: Path to the video file
            metadata_path: Path to the metadata JSON file
            research_data: Optional research data for SEO enhancement
            
        Returns:
            Upload result dictionary
        """
        if not self.youtube_service:
            if not self.authenticate():
                return {"success": False, "error": "Authentication failed"}
        
        try:
            # Load metadata
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            
            logger.info(f"Starting upload for: {metadata.get('title', 'Unknown')}")
            
            # Optimize metadata for SEO
            optimized_metadata = self.optimize_metadata_for_seo(metadata, research_data)
            
            # Prepare video snippet
            snippet = {
                'title': optimized_metadata['optimized_title'],
                'description': optimized_metadata['optimized_description'],
                'tags': optimized_metadata['optimized_tags'],
                'categoryId': config.YOUTUBE_CONFIG['category_id'],
                'defaultLanguage': config.YOUTUBE_CONFIG['default_language']
            }
            
            # Prepare status
            status = {
                'privacyStatus': config.YOUTUBE_CONFIG['privacy_status'],
                'license': config.YOUTUBE_CONFIG['license'],
                'embeddable': config.YOUTUBE_CONFIG['embeddable'],
                'publicStatsViewable': config.YOUTUBE_CONFIG['public_stats_viewable'],
                'madeForKids': config.YOUTUBE_CONFIG['made_for_kids']
            }
            
            # Create media upload object
            media = MediaFileUpload(
                str(video_path),
                chunksize=-1,
                resumable=True,
                mimetype='video/mp4'
            )
            
            # Create insert request
            insert_request = self.youtube_service.videos().insert(
                part='snippet,status',
                body={'snippet': snippet, 'status': status},
                media_body=media
            )
            
            # Execute upload with progress tracking
            logger.info("Uploading video to YouTube...")
            response = None
            error = None
            retry = 0
            
            while response is None:
                try:
                    status_upload, response = insert_request.next_chunk()
                    if status_upload:
                        progress = int(status_upload.progress() * 100)
                        logger.info(f"Upload progress: {progress}%")
                        
                except HttpError as e:
                    if e.resp.status in [500, 502, 503, 504]:
                        # Retriable errors
                        error = f"Retriable error {e.resp.status}: {e}"
                        retry += 1
                        if retry > 3:
                            break
                        time.sleep(2 ** retry)
                    else:
                        # Non-retriable error
                        error = f"Non-retriable error {e.resp.status}: {e}"
                        break
                except Exception as e:
                    error = f"Upload error: {e}"
                    break
            
            if response:
                video_id = response['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                
                logger.info(f"✅ Video uploaded successfully!")
                logger.info(f"📺 Video ID: {video_id}")
                logger.info(f"🔗 Video URL: {video_url}")
                
                # Try to upload thumbnail
                thumbnail_path = self.create_thumbnail(video_path)
                if thumbnail_path and thumbnail_path.exists():
                    try:
                        self.youtube_service.thumbnails().set(
                            videoId=video_id,
                            media_body=MediaFileUpload(str(thumbnail_path))
                        ).execute()
                        logger.info("✅ Custom thumbnail uploaded")
                    except Exception as e:
                        logger.warning(f"Failed to upload thumbnail: {e}")
                
                # Save upload metadata
                upload_metadata = {
                    'video_id': video_id,
                    'video_url': video_url,
                    'upload_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'optimized_title': optimized_metadata['optimized_title'],
                    'optimized_description': optimized_metadata['optimized_description'],
                    'tags': optimized_metadata['optimized_tags'],
                    'hashtags': optimized_metadata['trending_hashtags'],
                    'privacy_status': status['privacyStatus'],
                    'original_metadata': metadata
                }
                
                upload_metadata_path = video_path.parent / f"{video_path.stem}_upload.json"
                with open(upload_metadata_path, 'w') as f:
                    json.dump(upload_metadata, f, indent=2)
                
                return {
                    'success': True,
                    'video_id': video_id,
                    'video_url': video_url,
                    'metadata': upload_metadata
                }
            
            else:
                logger.error(f"Upload failed: {error}")
                return {'success': False, 'error': error}
                
        except Exception as e:
            logger.error(f"Error uploading video: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_upload_quota_usage(self) -> Dict:
        """Check YouTube API quota usage"""
        if not self.youtube_service:
            return {"error": "Not authenticated"}
        
        try:
            # This is a placeholder - YouTube doesn't provide direct quota info
            # You would need to track this manually or use Cloud Console
            return {
                "status": "quota_check_not_available",
                "message": "YouTube API doesn't provide direct quota usage. Check Google Cloud Console."
            }
        except Exception as e:
            return {"error": str(e)}