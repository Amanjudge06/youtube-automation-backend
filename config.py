"""
Configuration file for YouTube Shorts Automation System
All API keys and system settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ===========================
# API Keys (Set via environment variables or directly here)
# ===========================

# SERP API (for trends and image search)
SERP_API_KEY = os.getenv("SERP_API_KEY", "")

# OpenAI API (for script generation)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# ElevenLabs API (for voiceover)
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# Perplexity API (for trending topic research)
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

# Pexels API (for high-quality stock photos)
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")  # Get free at https://www.pexels.com/api/

# Unsplash API (for professional photography)
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")  # Get free at https://unsplash.com/developers

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# YouTube Data API v3 (for video uploads) - SaaS Configuration
# These credentials belong to the SaaS provider (you), not individual users
# Users will authenticate through this single OAuth application
YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REDIRECT_URI = os.getenv("YOUTUBE_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob")  # Out-of-band flow for demos
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "")  # For headless authentication on Cloud Run

# ===========================
# Trending Topics Settings
# ===========================

TRENDING_CONFIG = {
    "region": "US",  # UNITED STATES - change to US, GB, etc.
    "language": "en",
    "max_topics": 10,
    "serp_engine": "google_trends_trending_now",  # or "google_news"
    
    # ===========================
    # VELOCITY-BASED ANALYSIS SETTINGS
    # ===========================
    "velocity_mode": True,  # Enable velocity-based ranking (growth rate over static volume)
    "velocity_weights": {
        "base_velocity": 40,      # Max points from volume/hour rate (40%)
        "acceleration": 25,       # Max points from recent activity burst (25%) 
        "freshness": 20,          # Max points from content recency (20%)
        "direction": 15           # Max points from trend direction (15%)
    },
    "velocity_thresholds": {
        "explosive": 150000,      # 150K+ searches/hour = explosive trend
        "viral": 100000,          # 100K+ searches/hour = viral trend  
        "rising": 50000,          # 50K+ searches/hour = rising trend
        "steady": 10000           # 10K+ searches/hour = steady interest
    },
    "time_windows": {
        "explosive_window": 6,    # Analyze explosive trends in 6h windows
        "rising_window": 12,      # Analyze rising trends in 12h windows  
        "default_window": 24,     # Default analysis window in hours
        "declining_window": 48    # Extended window for declining trends
    },
    "velocity_priorities": {
        "prioritize_momentum": True,     # Favor fast-growing over high-static volume
        "early_detection": True,         # Catch trends in acceleration phase
        "news_velocity_boost": 1.3,      # 30% boost for topics with breaking news
        "recency_multiplier": 1.5        # 50% boost for very fresh content
    }
}

# ===========================
# Script Generation Settings
# ===========================

SCRIPT_CONFIG = {
    "model": "gpt-4o-mini",  # Updated working model (was gpt-4-turbo-preview)
    "temperature": 0.7,
    "max_tokens": 1500,  # Increased for longer scripts (approx 1000 words capacity)
    "script_duration_seconds": 58,  # Target 58 seconds (just under 60s limit)
    "tone": "energetic and engaging",
    "language": "english",  # "english", "hinglish" (hindi+english mix)
    "hinglish_ratio": 0.8,  # 80% Hindi words when using hinglish (0.1=10%, 0.5=50%, 0.8=80%)
}

# ===========================
# Topic Research Settings (Perplexity)
# ===========================

RESEARCH_CONFIG = {
    "model": "sonar",  # Perplexity model for web search - working correctly
    "temperature": 0.1,  # Lower temperature for more factual responses
    "max_tokens": 1000,
    "search_depth": "deep",  # basic, comprehensive, or deep
    "include_sources": True,
}

# ===========================
# Voiceover Settings
# ===========================

VOICEOVER_CONFIG = {
    "voice_id": "CAQWjBP1lNb75f6arc7F",  # Aman Voice - Male American
    "model_id": "eleven_turbo_v2_5",  # Most compatible expressive model
    "stability": 0.4,  # Creative setting for maximum expressiveness
    "similarity_boost": 0.8,  # Higher for better voice consistency
    "style": 0.2,  # Style exaggeration for more natural delivery
    "use_speaker_boost": True,  # Enable speaker enhancement
    "enable_emotion_tags": True,  # Enable v3-style emotion tags
    "emotion_intensity": 0.6,  # Control emotion strength
}

# ===========================
# Image Search Settings
# ===========================

IMAGE_CONFIG = {
    "num_images": 10,  # Images per video - increased for more engagement
    "safe_search": "active",
    "image_type": "photo",  # photo, clipart, face, etc.
    "image_size": "large",
    "usage_rights": "",  # Remove strict usage rights filter for better coverage
    "enforce_copyright_free": False,  # Allow wider range of images for better results
}

# ===========================
# Google Trends Category Mapping
# ===========================

TRENDS_CATEGORIES = {
    "1": "Autos and Vehicles",
    "2": "Beauty and Fashion", 
    "3": "Business and Finance",
    "20": "Climate",
    "4": "Entertainment",
    "5": "Food and Drink",
    "6": "Games",
    "7": "Health",
    "8": "Hobbies and Leisure",
    "9": "Jobs and Education",
    "10": "Law and Government",
    "11": "Other",
    "13": "Pets and Animals",
    "14": "Politics",
    "15": "Science",
    "16": "Shopping",
    "17": "Sports",
    "18": "Technology",
    "19": "Travel and Transportation"
}

# Category-specific content configuration
CATEGORY_CONFIG = {
    "17": {  # Sports
        "script_tone": "high-energy sports commentary",
        "image_focus": "match highlights, players, stadium, scoreboard, celebration",
        "keywords": ["match", "player", "goal", "score", "team", "stadium", "celebration", "victory", "defeat"]
    },
    "6": {  # Games
        "script_tone": "gaming excitement and hype",
        "image_focus": "gameplay screenshots, character art, game logos, gaming setups",
        "keywords": ["game", "gameplay", "character", "level", "boss", "achievement", "update", "release"]
    },
    "18": {  # Technology  
        "script_tone": "tech enthusiast review style",
        "image_focus": "product photos, specs, comparisons, launch events",
        "keywords": ["device", "specs", "features", "launch", "price", "review", "upgrade", "innovation"]
    },
    "4": {  # Entertainment
        "script_tone": "celebrity gossip and entertainment buzz",
        "image_focus": "celebrity photos, movie posters, red carpet, award shows",
        "keywords": ["celebrity", "movie", "show", "actor", "actress", "premiere", "award", "scandal"]
    },
    "16": {  # Shopping
        "script_tone": "deal hunter and product review excitement",
        "image_focus": "product photos, shopping deals, price comparisons, store displays, sale signs",
        "keywords": ["deal", "sale", "discount", "product", "price", "shopping", "store", "brand", "offer", "bargain"]
    },
    "default": {
        "script_tone": "energetic and engaging news style",
        "image_focus": "news photos, events, people, breaking news graphics",
        "keywords": ["news", "event", "breaking", "update", "announcement", "development"]
    }
}

# ===========================
# Video Assembly Settings
# ===========================

VIDEO_CONFIG = {
    "width": 1080,
    "height": 1920,  # 9:16 aspect ratio for YouTube Shorts
    "fps": 30,
    "image_duration": 6,  # seconds per image - faster for better engagement
    "fade_duration": 0.3,  # faster crossfade between images
    "background_music": None,  # Path to background music file (optional)
    "background_music_volume": 0.1,
    "subscribe_background": "assets/subscribe_background.png",  # Subscribe background image
    "subtitle_settings": {
        "font_size": 48,
        "font_color": "white",
        "font_weight": "bold",
        "position_y": 1400,  # Position subtitles in lower area
        "max_width": 950,  # Maximum width for subtitle text
        "outline_color": "black",
        "outline_width": 2
    }
}

# ===========================
# Output Settings
# ===========================

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

OUTPUT_CONFIG = {
    "video_format": "mp4",
    "video_codec": "libx264",
    "audio_codec": "aac",
    "bitrate": "5000k",
}

# ===========================
# Logging Settings
# ===========================

LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": LOGS_DIR / "youtube_automation.log",
}

# ===========================
# Topic Selection Settings
# ===========================

TOPIC_SELECTION = {
    "use_ai_scoring": True,  # Use AI to score topics for virality
    "auto_select": True,  # Automatically select best topic
    "blacklist_keywords": ["nsfw"],  # Topics to avoid
}

# ===========================
# YouTube Upload Settings
# ===========================

YOUTUBE_CONFIG = {
    "privacy_status": "public",  # "private", "unlisted", "public"
    "category_id": "24",  # Entertainment category (24), Gaming (20), News (25)
    "default_language": "en",
    "license": "creativeCommon",  # "youtube" or "creativeCommon" 
    "embeddable": True,
    "public_stats_viewable": True,
    "made_for_kids": False,
    "auto_levels": True,
    "stabilize": False,
    "thumbnail_size": (1280, 720),  # HD thumbnail
}

YOUTUBE_SEO_CONFIG = {
    "max_title_length": 100,
    "max_description_length": 5000,
    "max_tags": 10,
    "trending_hashtags_count": 5,
    "default_tags": ["shorts", "viral", "trending", "news", "breaking"],
    "include_location": True,
    "include_timestamps": True,
}

YOUTUBE_UPLOAD_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/youtube.force-ssl",  # Full YouTube access
]
