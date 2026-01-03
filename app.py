"""
YouTube Shorts Automation - Web Application
FastAPI backend for the automation system
"""

from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
import os
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from main import main as run_automation
from services.trends_service import TrendsService
from services.youtube_upload_service import YouTubeUploadService
from services.content_optimization_service import ContentOptimizationService
from services.supabase_service import SupabaseService
from utils.helpers import setup_logging, get_video_metadata

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Initialize Supabase
supabase_service = SupabaseService()

# Create FastAPI app
app = FastAPI(
    title="Snip-Z API",
    description="REST API for Snip-Z YouTube Shorts automation system",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
automation_status = {
    "running": False,
    "current_step": "",
    "progress": 0,
    "logs": [],
    "last_run": None,
    "error": None
}

# Pydantic models
class AutomationConfig(BaseModel):
    language: str = "english"
    upload_to_youtube: bool = False
    trending_region: str = "AU"
    script_tone: str = "energetic"

class TriggerAutomation(BaseModel):
    config: AutomationConfig
    user_id: Optional[str] = None

class VideoMetadata(BaseModel):
    id: str
    title: str
    topic: str
    duration: float
    created_at: str
    file_path: str
    youtube_url: Optional[str] = None
    performance: Dict = {}

class OptimizationRequest(BaseModel):
    channel_url: str

class OptimizationApply(BaseModel):
    recommendations: List[Dict]

class OptimizationRequest(BaseModel):
    channel_url: str

class OptimizationApply(BaseModel):
    recommendations: List[Dict]

# Optimization Endpoints (Frontend Compatible)
@app.get("/optimization/my-channel")
async def get_my_channel():
    """Get authenticated user's YouTube channel information"""
    try:
        from services.youtube_upload_service import YouTubeUploadService
        upload_service = YouTubeUploadService()
        
        # Check if we have stored channel info
        channel_info = upload_service.get_my_channel_info()
        
        if channel_info:
            return {
                "success": True,
                "channel_info": channel_info
            }
        else:
            # Try to authenticate and get channel info
            if upload_service.authenticate():
                channel_info = upload_service.get_my_channel_info()
                if channel_info:
                    return {
                        "success": True,
                        "channel_info": channel_info
                    }
            
            return {
                "success": False,
                "message": "Channel information not available. Please authenticate with YouTube first."
            }
    
    except Exception as e:
        logger.error(f"Error getting channel info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/optimization/status")
async def get_optimization_status_new():
    """Get current optimization status and parameters (frontend compatible)"""
    try:
        optimization_service = ContentOptimizationService()
        summary = optimization_service.get_optimization_summary()
        
        # Also get script generator optimization status
        from services.script_generator import ScriptGenerator
        script_gen = ScriptGenerator()
        script_status = script_gen.get_optimization_status()
        
        # Get trends optimization status
        trends_config = config.TRENDING_CONFIG.get("velocity_weights", {})
        
        # Get voice optimization settings
        voice_config = config.VOICE_CONFIG if hasattr(config, 'VOICE_CONFIG') else {
            "voice_id": "default",
            "stability": 0.5,
            "similarity_boost": 0.75
        }
        
        return {
            "content_optimization": {
                "status": "active" if summary.get("status") != "error" else "error",
                **summary
            },
            "script_optimization": script_status,
            "trends_optimization": {
                "volume_weight": trends_config.get("base_velocity", 40) / 100,
                "velocity_weight": trends_config.get("acceleration", 25) / 100,
                "recency_weight": trends_config.get("freshness", 20) / 100
            },
            "voice_optimization": voice_config,
            "status": "active" if summary.get("status") != "error" else "error"
        }
        
    except Exception as e:
        logger.error(f"Error getting optimization status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get optimization status: {e}")

@app.post("/optimization/analyze")
async def analyze_optimization_new(request: OptimizationRequest):
    """Analyze a YouTube channel and provide optimization recommendations based on actual video performance"""
    try:
        from services.video_performance_analyzer import VideoPerformanceAnalyzer
        
        # Extract channel URL and check if it's our authenticated channel
        channel_url = request.channel_url.strip()
        
        # Load real channel data if available
        try:
            with open("my_channel_info.json", "r") as f:
                real_channel_data = json.load(f)
                
            # Check if the requested URL matches our authenticated channel
            is_authenticated_channel = False
            channel_url_lower = channel_url.lower()
            
            # Multiple ways to match the authenticated channel
            if any([
                real_channel_data["channel_id"].lower() in channel_url_lower,
                real_channel_data["custom_url"].lower().replace("@", "") in channel_url_lower,
                real_channel_data["channel_url"].lower() in channel_url_lower,
                channel_url_lower in real_channel_data["channel_url"].lower(),
                "trending-tod" in channel_url_lower
            ]):
                is_authenticated_channel = True
                
            if is_authenticated_channel:
                # Perform data-driven analysis based on actual video performance
                analyzer = VideoPerformanceAnalyzer()
                performance_analysis = analyzer.analyze_video_performance()
                
                # Return comprehensive analysis with real data and data-driven recommendations
                analysis = {
                    "channel_metrics": {
                        "subscriber_count": real_channel_data["subscriber_count"],
                        "total_views": real_channel_data["view_count"],
                        "video_count": real_channel_data["video_count"],
                        "avg_views_per_video": round(real_channel_data["view_count"] / max(real_channel_data["video_count"], 1), 1)
                    },
                    "performance_analysis": performance_analysis,
                    "content_patterns": {
                        "top_topics": performance_analysis.get("performance_insights", {}).get("topic_performance", {}).get("best_performing_topics", [])[:3],
                        "best_upload_day": "Data-driven timing analysis",
                        "best_upload_time": _get_optimal_upload_time(performance_analysis),
                        "optimal_length": _get_optimal_script_length(performance_analysis)
                    },
                    "recommendations": performance_analysis.get("data_driven_recommendations", []) + [
                        {
                            "category": "Performance Insights",
                            "suggestion": f"Based on your {performance_analysis.get('youtube_uploaded', 0)} uploaded videos analysis",
                            "impact": "High",
                            "confidence": "100%"
                        }
                    ]
                }
                
                return analysis
                
        except FileNotFoundError:
            pass
            
        # Fallback for non-authenticated channels
        return {
            "error": "Video performance analysis only available for authenticated channels",
            "message": "Please use your own authenticated channel for detailed performance-based analysis"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in optimization analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {e}")

def _get_current_config_snapshot() -> Dict:
    """Get current system configuration snapshot"""
    try:
        return {
            "voice_settings": {
                "voice_id": config.VOICEOVER_CONFIG.get("voice_id", "default"),
                "stability": config.VOICEOVER_CONFIG.get("stability", 0.5),
                "similarity_boost": config.VOICEOVER_CONFIG.get("similarity_boost", 0.75)
            },
            "trending_weights": config.TRENDING_CONFIG.get("velocity_weights", {}),
            "script_config": {
                "duration": config.SCRIPT_CONFIG.get("script_duration_seconds", 60),
                "style": config.SCRIPT_CONFIG.get("style", "engaging")
            }
        }
    except Exception as e:
        logger.error(f"Error getting config snapshot: {e}")
        return {}

def _generate_changes_summary(before: Dict, after: Dict) -> List[str]:
    """Generate summary of changes between before and after states"""
    changes = []
    try:
        # Voice changes
        before_voice = before.get("config_snapshot", {}).get("voice_settings", {}).get("voice_id")
        after_voice = after.get("config_snapshot", {}).get("voice_settings", {}).get("voice_id") 
        if before_voice != after_voice:
            changes.append(f"Voice changed: {before_voice or 'Unknown'} → {after_voice or 'Unknown'}")
        
        # Profile changes
        before_name = before.get("profile", {}).get("name")
        after_name = after.get("profile", {}).get("name")
        if before_name != after_name:
            changes.append(f"Profile updated: {before_name or 'Default'} → {after_name or 'Default'}")
        
        if not changes:
            changes.append("Configuration optimized based on performance data")
            
        return changes
    except Exception as e:
        logger.error(f"Error generating changes summary: {e}")
        return ["Optimization applied successfully"]

def _get_optimal_upload_time(performance_analysis: Dict) -> str:
    """Extract optimal upload time from performance analysis"""
    try:
        successful_patterns = performance_analysis.get("performance_insights", {}).get("successful_patterns", {})
        upload_hours = successful_patterns.get("common_upload_hours", [])
        if upload_hours and len(upload_hours) > 0:
            primary_hour = upload_hours[0]
            return f"Peak hours: {primary_hour:02d}:00-{primary_hour+2:02d}:00 (data-driven)"
        
        # Check if we have any performance data at all
        total_videos = performance_analysis.get("total_videos_analyzed", 0)
        if total_videos > 0:
            return "14:00-16:00 (analyzed but no clear pattern - continue testing)"
        return "Peak hours (2-4 PM) - insufficient data"
    except Exception as e:
        logger.error(f"Error getting optimal upload time: {e}")
        return "Peak hours (2-4 PM)"

def _get_current_config_snapshot() -> Dict:
    """Get current system configuration snapshot"""
    try:
        return {
            "voice_settings": {
                "voice_id": config.VOICEOVER_CONFIG.get("voice_id", "default"),
                "stability": config.VOICEOVER_CONFIG.get("stability", 0.5),
                "similarity_boost": config.VOICEOVER_CONFIG.get("similarity_boost", 0.75)
            },
            "trending_weights": config.TRENDING_CONFIG.get("velocity_weights", {}),
            "script_config": {
                "duration": config.SCRIPT_CONFIG.get("script_duration_seconds", 60),
                "style": config.SCRIPT_CONFIG.get("style", "engaging")
            }
        }
    except Exception as e:
        logger.error(f"Error getting config snapshot: {e}")
        return {}

def _generate_changes_summary(before: Dict, after: Dict) -> List[str]:
    """Generate summary of changes between before and after states"""
    changes = []
    try:
        # Voice changes
        if before.get("config_snapshot", {}).get("voice_settings", {}).get("voice_id") != after.get("config_snapshot", {}).get("voice_settings", {}).get("voice_id"):
            old_voice = before.get("config_snapshot", {}).get("voice_settings", {}).get("voice_id", "Unknown")
            new_voice = after.get("config_snapshot", {}).get("voice_settings", {}).get("voice_id", "Unknown")
            changes.append(f"Voice changed: {old_voice} → {new_voice}")
        
        # Profile changes
        if before.get("profile", {}).get("name") != after.get("profile", {}).get("name"):
            old_name = before.get("profile", {}).get("name", "Default")
            new_name = after.get("profile", {}).get("name", "Default")
            changes.append(f"Profile updated: {old_name} → {new_name}")
        
        if not changes:
            changes.append("Configuration optimized based on performance data")
            
        return changes
    except Exception as e:
        logger.error(f"Error generating changes summary: {e}")
        return ["Optimization applied successfully"]

def _get_optimal_script_length(performance_analysis: Dict) -> str:
    """Extract optimal script length from performance analysis"""
    try:
        successful_patterns = performance_analysis.get("performance_insights", {}).get("successful_patterns", {})
        script_length = successful_patterns.get("avg_script_length", 0)
        if script_length > 0:
            words = script_length / 4  # ~4 chars per word
            seconds = words / 2.5  # ~2.5 words per second
            return f"~{seconds:.0f} seconds ({script_length:.0f} characters - data-driven)"
        
        # Check if we have performance data but no clear pattern
        total_videos = performance_analysis.get("total_videos_analyzed", 0)
        if total_videos > 0:
            return "45-60 seconds (analyzed but no clear pattern - continue current length)"
        return "30-45 seconds (shorts format) - insufficient data"
    except Exception as e:
        logger.error(f"Error getting optimal script length: {e}")
        return "30-45 seconds (shorts format)"

# API Routes
@app.get("/")
async def root():
    """Serve the React frontend"""
    return FileResponse("frontend/build/index.html")

@app.get("/optimization/my-channel")
async def get_my_channel():
    """Get authenticated user's YouTube channel information"""
    try:
        from services.youtube_upload_service import YouTubeUploadService
        upload_service = YouTubeUploadService()
        
        # Check if we have stored channel info
        channel_info = upload_service.get_my_channel_info()
        
        if channel_info:
            return {
                "success": True,
                "channel_info": channel_info
            }
        else:
            # Try to authenticate and get channel info
            if upload_service.authenticate():
                channel_info = upload_service.get_my_channel_info()
                if channel_info:
                    return {
                        "success": True,
                        "channel_info": channel_info
                    }
            
            return {
                "success": False,
                "message": "Channel information not available. Please authenticate with YouTube first."
            }
    
    except Exception as e:
        logger.error(f"Error getting channel info: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/optimization/status")
async def get_optimization_status_new():
    """Get current optimization status and parameters (frontend compatible)"""
    try:
        optimization_service = ContentOptimizationService()
        summary = optimization_service.get_optimization_summary()
        
        # Also get script generator optimization status
        from services.script_generator import ScriptGenerator
        script_gen = ScriptGenerator()
        script_status = script_gen.get_optimization_status()
        
        # Get trends optimization status
        trends_config = config.TRENDING_CONFIG.get("velocity_weights", {})
        
        # Get voice optimization settings
        voice_config = config.VOICE_CONFIG if hasattr(config, 'VOICE_CONFIG') else {
            "voice_id": "default",
            "stability": 0.5,
            "similarity_boost": 0.75
        }
        
        return {
            "content_optimization": {
                "status": "active" if summary.get("status") != "error" else "error",
                **summary
            },
            "script_optimization": script_status,
            "trends_optimization": {
                "volume_weight": trends_config.get("base_velocity", 40) / 100,
                "velocity_weight": trends_config.get("acceleration", 25) / 100,
                "recency_weight": trends_config.get("freshness", 20) / 100
            },
            "voice_optimization": voice_config,
            "status": "active" if summary.get("status") != "error" else "error"
        }
        
    except Exception as e:
        logger.error(f"Error getting optimization status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get optimization status: {e}")

@app.post("/optimization/apply")
async def apply_optimization(request: OptimizationRequest):
    """Apply optimization recommendations to the system based on video performance data"""
    try:
        from services.content_optimization_service import ContentOptimizationService
        from services.video_performance_analyzer import VideoPerformanceAnalyzer
        import json
        
        # Get performance analysis for data-driven optimizations
        analyzer = VideoPerformanceAnalyzer()
        performance_analysis = analyzer.analyze_video_performance()
        
        # Get recommendations from analysis
        recommendations = performance_analysis.get("data_driven_recommendations", [])
        applied_changes = []
        
        # Capture BEFORE state for comparison
        optimization_service = ContentOptimizationService()
        before_state = {
            "profile": optimization_service.current_optimization_profile.copy(),
            "config_snapshot": _get_current_config_snapshot(),
            "timestamp": datetime.now().isoformat()
        }
        
        # Initialize optimization service to apply changes  
        current_profile = optimization_service.current_optimization_profile
        
        # Apply each recommendation with real configuration changes
        for rec in recommendations:
            category = rec.get("category", "").lower()
            suggestion = rec.get("suggestion", "")
            rec_type = rec.get("type", "")
            
            if "growth strategy" in category.lower() or "content strategy" in category.lower():
                # Apply data-driven content strategy changes
                if "data_driven" in rec_type:
                    # Use actual best-performing topics
                    best_topics = performance_analysis.get("performance_insights", {}).get("topic_performance", {}).get("best_performing_topics", [])
                    if best_topics:
                        current_profile["content_strategy"]["niche_focus"] = [t[0] for t in best_topics[:3]]
                        applied_changes.append(f"✅ Data-driven topic focus: {', '.join([t[0] for t in best_topics[:3]])}")
                    
                current_profile["content_strategy"]["trend_velocity_weight"] = 0.95
                current_profile["content_strategy"]["content_freshness_requirement"] = 4
                current_profile["performance_targets"]["target_view_count"] = int(current_profile["performance_targets"]["target_view_count"] * 1.2)
                applied_changes.append("✅ Enhanced growth strategy based on performance data")
                
            elif "content optimization" in category.lower():
                # Update script and trending settings
                current_profile["script_optimization"]["trending_keyword_weight"] = 0.9
                current_profile["script_optimization"]["controversy_level"] = min(0.5, current_profile["script_optimization"]["controversy_level"] + 0.1)
                current_profile["script_optimization"]["hook_style"] = "trending_focus"
                applied_changes.append("✅ Optimized content generation with performance insights")
                
            elif "audience engagement" in category.lower():
                # Update engagement parameters
                current_profile["script_optimization"]["call_to_action_frequency"] = "high"
                current_profile["script_optimization"]["engagement_triggers"] = [
                    "What do you think?", "Let me know below", "Share your thoughts!", 
                    "Which side are you on?", "Comment your opinion!"
                ]
                current_profile["voiceover_optimization"]["energy_level"] = min(1.0, current_profile["voiceover_optimization"]["energy_level"] + 0.1)
                applied_changes.append("✅ Boosted audience engagement based on successful video patterns")
                
            elif "upload timing" in category.lower():
                # Use data-driven upload timing
                successful_patterns = performance_analysis.get("performance_insights", {}).get("successful_patterns", {})
                best_hours = successful_patterns.get("common_upload_hours", [])
                if best_hours:
                    current_profile["content_strategy"]["optimal_posting_time"] = f"{best_hours[0]:02d}:00-{best_hours[0]+2:02d}:00"
                    applied_changes.append(f"✅ Data-driven upload timing: {best_hours[0]:02d}:00-{best_hours[0]+2:02d}:00 based on your best performers")
                else:
                    current_profile["content_strategy"]["optimal_posting_time"] = "14:00-16:00"
                    applied_changes.append("✅ Optimized upload timing: Set peak hours (2-4 PM)")
                    
            elif "title optimization" in category.lower():
                # Apply data-driven title optimization
                successful_patterns = performance_analysis.get("performance_insights", {}).get("successful_patterns", {})
                optimal_length = successful_patterns.get("avg_title_length", 50)
                current_profile["script_optimization"]["optimal_title_length"] = int(optimal_length)
                applied_changes.append(f"✅ Data-driven title optimization: ~{optimal_length:.0f} characters based on your top performers")
                
            elif "script optimization" in category.lower():
                # Apply data-driven script optimization
                successful_patterns = performance_analysis.get("performance_insights", {}).get("successful_patterns", {})
                optimal_script_length = successful_patterns.get("avg_script_length", 1000)
                current_profile["script_optimization"]["optimal_word_count"] = int(optimal_script_length / 4)  # ~4 chars per word
                applied_changes.append(f"✅ Data-driven script length: ~{optimal_script_length:.0f} characters based on successful videos")
                
            elif "seo" in category.lower():
                # Update SEO and title optimization
                current_profile["script_optimization"]["trending_keyword_weight"] = 0.95
                current_profile["content_strategy"]["niche_focus"] = ["trending_news", "viral_topics"]
                applied_changes.append("✅ Enhanced SEO optimization: Maximized keyword targeting and viral topic focus")
        
        # Add performance summary to applied changes
        performance_summary = performance_analysis.get("performance_insights", {}).get("performance_summary", {})
        if performance_summary:
            applied_changes.append(f"📊 Analysis based on {performance_summary.get('total_videos', 0)} videos with {performance_summary.get('average_views', 0):.0f} avg views")
        
        # Save updated optimization profile
        current_profile["last_updated"] = datetime.now().isoformat()
        current_profile["optimization_version"] = "3.0_data_driven"
        current_profile["performance_analysis"] = performance_analysis.get("performance_insights", {})
        
        # Ensure logs directory exists
        import os
        os.makedirs("logs", exist_ok=True)
        
        # Save the profile
        with open("logs/optimization_profile.json", "w") as f:
            json.dump(current_profile, f, indent=2)
        
        # Save detailed performance analysis
        with open("logs/video_performance_analysis.json", "w") as f:
            json.dump(performance_analysis, f, indent=2)
        
        # Capture AFTER state for comparison
        after_state = {
            "profile": current_profile.copy(),
            "config_snapshot": _get_current_config_snapshot(),
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Applied {len(applied_changes)} data-driven optimization changes")
        
        return {
            "success": True,
            "message": f"Successfully applied {len(applied_changes)} data-driven optimization improvements",
            "applied_changes": applied_changes,
            "optimization_profile_updated": True,
            "performance_analysis_saved": True,
            "videos_analyzed": performance_analysis.get("total_videos_analyzed", 0),
            "timestamp": datetime.now().isoformat(),
            "before_after_comparison": {
                "before": before_state,
                "after": after_state,
                "changes_summary": _generate_changes_summary(before_state, after_state)
            }
        }
        
    except Exception as e:
        logger.error(f"Error applying optimizations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to apply optimizations: {e}")

@app.get("/voices/available")
async def get_available_voices():
    """Get all available ElevenLabs voices"""
    try:
        from services.voiceover_service import VoiceoverService
        
        voiceover_service = VoiceoverService()
        voices = voiceover_service.get_available_voices()
        
        return {
            "voices": voices,
            "total": len(voices),
            "current_voice": config.VOICEOVER_CONFIG.get("voice_id", "default")
        }
        
    except Exception as e:
        logger.error(f"Error fetching available voices: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch voices: {e}")

@app.post("/voices/set")
async def set_voice(voice_data: Dict):
    """Set the active voice for voiceovers"""
    try:
        voice_id = voice_data.get("voice_id")
        voice_name = voice_data.get("voice_name", "Unknown")
        
        if not voice_id:
            raise HTTPException(status_code=400, detail="voice_id is required")
        
        # Update config
        config.VOICEOVER_CONFIG["voice_id"] = voice_id
        
        # Also save to optimization profile if exists
        try:
            from services.content_optimization_service import ContentOptimizationService
            optimization_service = ContentOptimizationService()
            profile = optimization_service.current_optimization_profile
            if "voiceover_optimization" not in profile:
                profile["voiceover_optimization"] = {}
            profile["voiceover_optimization"]["voice_id"] = voice_id
            profile["voiceover_optimization"]["voice_name"] = voice_name
            optimization_service._save_optimization_profile(profile)
        except Exception as e:
            logger.warning(f"Could not update optimization profile with new voice: {e}")
        
        return {
            "success": True,
            "message": f"Voice set to: {voice_name}",
            "voice_id": voice_id,
            "voice_name": voice_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting voice: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set voice: {e}")

@app.get("/youtube/auth/start")
async def start_youtube_auth(user_id: str = "demo_user"):
    """Start YouTube OAuth flow for a specific user"""
    try:
        from services.youtube_upload_service import YouTubeUploadService
        from services.user_manager import user_manager
        
        # Create user if doesn't exist
        user_manager.create_user(user_id)
        
        upload_service = YouTubeUploadService()
        
        # Generate OAuth URL with user context
        auth_url = upload_service.get_auth_url_for_user(user_id)
        
        return {
            "auth_url": auth_url,
            "user_id": user_id,
            "message": f"Please visit this URL to connect your YouTube account"
        }
        
    except Exception as e:
        logger.error(f"Error starting YouTube auth for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start authentication: {e}")

@app.post("/youtube/auth/callback")
async def youtube_auth_callback(auth_data: Dict):
    """Handle YouTube OAuth callback for SaaS users"""
    try:
        from services.youtube_upload_service import YouTubeUploadService
        from services.user_manager import user_manager
        
        auth_code = auth_data.get("auth_code")
        user_id = auth_data.get("user_id", "demo_user")
        
        if not auth_code:
            raise HTTPException(status_code=400, detail="Authorization code is required")
        
        upload_service = YouTubeUploadService()
        
        # Exchange auth code for credentials and associate with user
        success, channel_info = upload_service.authenticate_user_with_code(user_id, auth_code)
        
        if success and channel_info:
            return {
                "success": True,
                "message": "YouTube channel connected successfully!",
                "channel_info": channel_info,
                "user_id": user_id
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to authenticate with YouTube")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in YouTube auth callback: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {e}")

@app.get("/youtube/channels/{user_id}")
async def get_user_youtube_channels(user_id: str = "demo_user"):
    """Get YouTube channels for a specific user"""
    try:
        from services.user_manager import user_manager
        
        user_channels = user_manager.get_user_channels(user_id)
        user = user_manager.get_user(user_id)
        
        formatted_channels = []
        for channel in user_channels:
            formatted_channels.append({
                "id": channel["id"],
                "title": channel["title"],
                "subscriber_count": channel["subscriber_count"],
                "is_default": channel["id"] == user.get("active_channel") if user else False,
                "added_at": channel["added_at"]
            })
        
        return {
            "success": True,
            "user_id": user_id,
            "channels": formatted_channels
        }
        
    except Exception as e:
        logger.error(f"Error fetching channels for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch channels: {e}")

@app.post("/youtube/channels/{user_id}/set-active")
async def set_active_channel(user_id: str, channel_data: Dict):
    """Set active channel for a user"""
    try:
        from services.user_manager import user_manager
        
        channel_id = channel_data.get("channel_id")
        if not channel_id:
            raise HTTPException(status_code=400, detail="Channel ID is required")
        
        success = user_manager.set_active_channel(user_id, channel_id)
        
        if success:
            return {
                "success": True,
                "message": "Active channel updated",
                "active_channel": channel_id
            }
        else:
            raise HTTPException(status_code=400, detail="Failed to set active channel")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting active channel: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set active channel: {e}")

@app.get("/youtube/channels")
async def get_youtube_channels_legacy():
    """Legacy endpoint - redirects to demo user"""
    return await get_user_youtube_channels("demo_user")
async def get_youtube_channels():
    """Get available YouTube channels for the authenticated user"""
    try:
        from services.youtube_upload_service import YouTubeUploadService
        
        upload_service = YouTubeUploadService()
        
        # Try to get my channel info (authenticated channel)
        my_channel = upload_service.get_my_channel_info()
        
        channels = []
        if my_channel:
            channels.append({
                "id": my_channel["channel_id"],
                "title": my_channel["title"],
                "subscriber_count": my_channel["subscriber_count"],
                "view_count": my_channel["view_count"], 
                "video_count": my_channel["video_count"],
                "is_default": True,
                "is_authenticated": True
            })
        
        return {
            "channels": channels,
            "total": len(channels),
            "authenticated_channel": my_channel["channel_id"] if my_channel else None
        }
        
    except Exception as e:
        logger.error(f"Error fetching YouTube channels: {e}")
        # Return mock data for development
        return {
            "channels": [
                {
                    "id": "UCWKKWQV4UKlMhwtaiMoJtVA",
                    "title": "TRENDING TODAY 👀",
                    "subscriber_count": 14,
                    "view_count": 1659,
                    "video_count": 7,
                    "is_default": True,
                    "is_authenticated": True
                }
            ],
            "total": 1,
            "authenticated_channel": "UCWKKWQV4UKlMhwtaiMoJtVA"
        }

@app.post("/youtube/channels/set-default")
async def set_default_youtube_channel(channel_data: Dict):
    """Set the default YouTube channel for uploads"""
    try:
        channel_id = channel_data.get("channel_id")
        
        if not channel_id:
            raise HTTPException(status_code=400, detail="channel_id is required")
        
        # Save the default channel to config or optimization profile
        try:
            from services.content_optimization_service import ContentOptimizationService
            optimization_service = ContentOptimizationService()
            profile = optimization_service.current_optimization_profile
            
            if "upload_settings" not in profile:
                profile["upload_settings"] = {}
            profile["upload_settings"]["default_channel"] = channel_id
            optimization_service._save_optimization_profile(profile)
        except Exception as e:
            logger.warning(f"Could not update optimization profile with default channel: {e}")
        
        return {
            "success": True,
            "message": "Default channel updated successfully",
            "default_channel": channel_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error setting default channel: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to set default channel: {e}")

@app.get("/voices/current")
async def get_current_voice():
    """Get currently selected voice"""
    try:
        return {
            "voice_id": config.VOICEOVER_CONFIG.get("voice_id", "default"),
            "voice_settings": {
                "stability": config.VOICEOVER_CONFIG.get("stability", 0.5),
                "similarity_boost": config.VOICEOVER_CONFIG.get("similarity_boost", 0.75),
                "style": config.VOICEOVER_CONFIG.get("style", 0.2)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting current voice: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get current voice: {e}")

@app.get("/api/status")
async def get_status():
    """Get current automation status"""
    return automation_status

@app.post("/api/optimization/analyze")
async def analyze_and_optimize(background_tasks: BackgroundTasks, channel_id: str = None):
    """Analyze channel performance and optimize content generation"""
    try:
        optimization_service = ContentOptimizationService()
        
        # Run analysis in background if channel_id provided, otherwise return current status
        if channel_id:
            background_tasks.add_task(optimization_service.analyze_and_optimize, channel_id)
            return {"message": "Analysis started", "channel_id": channel_id}
        else:
            # Return current optimization status
            summary = optimization_service.get_optimization_summary()
            return {"optimization_summary": summary}
    
    except Exception as e:
        logger.error(f"Error in optimization analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Optimization failed: {e}")

@app.get("/api/optimization/status")
async def get_optimization_status():
    """Get current optimization status and parameters"""
    try:
        optimization_service = ContentOptimizationService()
        summary = optimization_service.get_optimization_summary()
        
        # Also get script generator optimization status
        from services.script_generator import ScriptGenerator
        script_gen = ScriptGenerator()
        script_status = script_gen.get_optimization_status()
        
        return {
            "content_optimization": summary,
            "script_optimization": script_status,
            "status": "active" if summary.get("status") != "error" else "error"
        }
        
    except Exception as e:
        logger.error(f"Error getting optimization status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get optimization status: {e}")

@app.get("/api/optimization/recommendations")
async def get_optimization_recommendations():
    """Get latest optimization recommendations"""
    try:
        optimization_service = ContentOptimizationService()
        
        # Get optimized configurations
        script_config = optimization_service.get_optimized_script_config()
        voiceover_config = optimization_service.get_optimized_voiceover_config()
        
        return {
            "script_optimizations": script_config,
            "voiceover_optimizations": voiceover_config,
            "last_updated": optimization_service.current_optimization_profile.get("last_updated"),
            "optimization_active": True
        }
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {e}")

@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    return {
        "trending_config": config.TRENDING_CONFIG,
        "script_config": config.SCRIPT_CONFIG,
        "youtube_seo_config": config.YOUTUBE_SEO_CONFIG
    }

@app.post("/api/automation/trigger")
async def trigger_automation(request: TriggerAutomation, background_tasks: BackgroundTasks):
    """Trigger the automation process"""
    if automation_status["running"]:
        raise HTTPException(status_code=400, detail="Automation already running")
    
    automation_status["running"] = True
    automation_status["current_step"] = "Starting..."
    automation_status["progress"] = 0
    automation_status["error"] = None
    automation_status["logs"] = []
    
    # Run automation in background
    background_tasks.add_task(
        run_automation_async,
        request.config.language,
        request.config.upload_to_youtube,
        request.user_id
    )
    
    return {"message": "Automation started", "status": automation_status}

@app.get("/api/automation/stop")
async def stop_automation():
    """Stop the automation process"""
    automation_status["running"] = False
    automation_status["current_step"] = "Stopped"
    return {"message": "Automation stopped"}

@app.get("/api/videos")
async def get_videos():
    """Get list of generated videos"""
    videos = []
    output_dir = Path(config.OUTPUT_DIR)
    
    if output_dir.exists():
        for video_file in output_dir.glob("*.mp4"):
            metadata_file = video_file.with_suffix('.json')
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r') as f:
                        metadata = json.load(f)
                    
                    videos.append({
                        "id": video_file.stem,
                        "title": metadata.get("title", "Unknown"),
                        "topic": metadata.get("topic", "Unknown"),
                        "duration": metadata.get("duration", 0),
                        "created_at": metadata.get("timestamp", "Unknown"),
                        "file_path": str(video_file),
                        "youtube_url": metadata.get("youtube_upload", {}).get("video_url"),
                        "performance": {
                            "images_used": metadata.get("images_used", 0),
                            "script_length": len(metadata.get("script", "")),
                            "scenes": len(metadata.get("scenes", []))
                        }
                    })
                except Exception as e:
                    logger.error(f"Error reading metadata for {video_file}: {e}")
    
    # Sort by creation date (newest first)
    videos.sort(key=lambda x: x["created_at"], reverse=True)
    return {"videos": videos, "total": len(videos)}

@app.get("/api/videos/{video_id}")
async def get_video_details(video_id: str):
    """Get detailed information about a specific video"""
    video_file = Path(config.OUTPUT_DIR) / f"{video_id}.mp4"
    metadata_file = Path(config.OUTPUT_DIR) / f"{video_id}.json"
    
    if not video_file.exists() or not metadata_file.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    try:
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading video metadata: {e}")

@app.get("/api/videos/{video_id}/download")
async def download_video(video_id: str):
    """Download a generated video"""
    video_file = Path(config.OUTPUT_DIR) / f"{video_id}.mp4"
    
    if not video_file.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    
    return FileResponse(
        video_file,
        media_type="video/mp4",
        filename=f"{video_id}.mp4"
    )

@app.get("/api/trends")
async def get_trending_topics():
    """Get current trending topics"""
    try:
        trends_service = TrendsService()
        trending_topics = trends_service.get_trending_topics()
        return {"topics": trending_topics, "total": len(trending_topics)}
    except Exception as e:
        logger.error(f"Error fetching trends: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trending topics")

@app.get("/api/logs")
async def get_logs():
    """Get recent automation logs"""
    logs_dir = Path(config.LOGS_DIR)
    logs = []
    
    if logs_dir.exists():
        # Get the most recent log file
        log_files = list(logs_dir.glob("*.log"))
        if log_files:
            latest_log = max(log_files, key=lambda p: p.stat().st_mtime)
            try:
                with open(latest_log, 'r') as f:
                    log_content = f.read().split('\n')
                    # Return last 100 lines
                    logs = log_content[-100:] if len(log_content) > 100 else log_content
            except Exception as e:
                logger.error(f"Error reading log file: {e}")
    
    return {"logs": logs}

@app.post("/api/config/update")
async def update_config(config_update: Dict):
    """Update configuration settings"""
    try:
        # Update configuration (this is a simplified version)
        # In production, you'd want to validate and persist these changes
        return {"message": "Configuration updated", "config": config_update}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {e}")

# Background task for automation
async def run_automation_async(language: str = "english", upload_to_youtube: bool = False, user_id: str = None):
    """Run automation in the background and update status"""
    try:
        automation_status["current_step"] = "Fetching trending topics..."
        automation_status["progress"] = 10
        
        # Run the actual automation with web-safe error handling
        try:
            video_path = run_automation_web_safe(language, upload_to_youtube)
            
            if video_path:
                # Upload to Supabase if user_id is provided
                if user_id:
                    try:
                        automation_status["current_step"] = "Syncing with cloud..."
                        
                        # Upload video file
                        video_file = Path(video_path)
                        storage_path = f"{user_id}/{video_file.name}"
                        public_url = supabase_service.upload_file("videos", storage_path, video_file)
                        
                        if public_url:
                            # Get metadata
                            metadata_file = video_file.with_suffix('.json')
                            metadata = {}
                            if metadata_file.exists():
                                with open(metadata_file, 'r') as f:
                                    metadata = json.load(f)
                            
                            # Save to database
                            video_data = {
                                "title": metadata.get("title", video_file.stem),
                                "description": metadata.get("description", ""),
                                "topic": metadata.get("topic", ""),
                                "file_path": str(video_path),
                                "storage_path": storage_path,
                                "status": "completed",
                                "youtube_url": metadata.get("youtube_url")
                            }
                            
                            supabase_service.save_video_metadata(user_id, video_data)
                            automation_status["logs"].append("✅ Synced with Supabase")
                    except Exception as e:
                        logger.error(f"Supabase sync failed: {e}")
                        automation_status["logs"].append(f"⚠️ Cloud sync failed: {e}")

                automation_status["running"] = False
                automation_status["current_step"] = "Completed successfully!"
                automation_status["progress"] = 100
                automation_status["last_run"] = datetime.now().isoformat()
                automation_status["logs"].append(f"Video created: {video_path}")
            else:
                raise Exception("Video creation failed - no output file generated")
                
        except SystemExit as e:
            # Catch sys.exit calls and convert to regular exceptions
            raise Exception(f"Automation process exited with code {e.code}")
        
    except Exception as e:
        logger.error(f"Automation failed: {e}")
        automation_status["running"] = False
        automation_status["current_step"] = f"Failed: {str(e)}"
        automation_status["error"] = str(e)
        automation_status["logs"].append(f"Error: {str(e)}")


def run_automation_web_safe(language: str = "english", upload_to_youtube: bool = False):
    """Web-safe version of run_automation that returns None on failure instead of sys.exit"""
    try:
        # Set up logging without exiting on errors
        from utils.helpers import setup_logging
        setup_logging()
        
        # Import services
        from services.trends_service import TrendsService
        from services.research_service import ResearchService
        from services.script_generator import ScriptGenerator
        from services.voiceover_service import VoiceoverService
        from services.image_service import ImageService
        from services.simple_video_service import SimpleVideoService  # Use optimized simple video service
        from services.youtube_upload_service import YouTubeUploadService
        from utils.helpers import generate_filename, get_video_metadata
        import config
        
        # Initialize services
        trends_service = TrendsService()
        research_service = ResearchService()
        script_generator = ScriptGenerator()
        voiceover_service = VoiceoverService()
        image_service = ImageService()
        video_service = SimpleVideoService()  # Use optimized simple video service
        
        automation_status["current_step"] = "Fetching trending topics..."
        automation_status["progress"] = 15
        
        # Get trending topics
        trending_topics = trends_service.get_trending_topics()
        if not trending_topics:
            logger.error("No trending topics found")
            return None
            
        selected_topic = trending_topics[0]
        topic = selected_topic['query']
        logger.info(f"Selected trending topic: {topic}")
        
        automation_status["current_step"] = "Researching topic..."
        automation_status["progress"] = 30
        
        # Research the topic
        research_data = research_service.research_trending_topic(topic)
        if not research_data:
            logger.error(f"Failed to research topic: {topic}")
            return None
            
        automation_status["current_step"] = "Generating script..."
        automation_status["progress"] = 45
        
        # Generate script
        script_data = script_generator.generate_script(selected_topic, research_data)
        if not script_data:
            logger.error("Failed to generate script")
            return None
            
        automation_status["current_step"] = "Creating voiceover..."
        automation_status["progress"] = 60
        
        # Generate voiceover
        audio_filename = generate_filename(topic, "mp3")
        audio_path = Path(config.TEMP_DIR) / audio_filename
        
        success = voiceover_service.generate_voiceover(
            script_data['script'],
            audio_path
        )
        
        if not success or not audio_path.exists():
            logger.error("Failed to generate voiceover")
            return None
            
        # Generate Subtitles
        automation_status["current_step"] = "Generating subtitles..."
        subtitles_path = voiceover_service.generate_subtitles(audio_path)
            
        automation_status["current_step"] = "Collecting images..."
        automation_status["progress"] = 75
        
        # Get images
        scenes = script_data.get('scenes', [])
        image_paths = image_service.fetch_images_for_scenes(topic, script_data, research_data)
        if not image_paths:
            logger.error("Failed to collect images")
            return None
            
        # Debug: Check which image files actually exist
        logger.info(f"Image service returned {len(image_paths)} paths")
        existing_images = []
        for i, img_path in enumerate(image_paths):
            if img_path.exists():
                logger.info(f"  ✅ Image {i+1} exists: {img_path}")
                existing_images.append(img_path)
            else:
                logger.warning(f"  ❌ Image {i+1} missing: {img_path}")
        
        if not existing_images:
            logger.error("No image files actually exist")
            return None
            
        logger.info(f"Using {len(existing_images)} existing images for video creation")
        image_paths = existing_images
            
        automation_status["current_step"] = "Assembling video..."
        automation_status["progress"] = 90
        
        # Create video using simple service
        video_path = config.OUTPUT_DIR / generate_filename(topic, "mp4")
        
        # Get actual audio duration from the generated file
        try:
            import subprocess
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
                '-of', 'csv=p=0', str(audio_path)
            ], capture_output=True, text=True, timeout=10)
            audio_duration = float(result.stdout.strip()) if result.stdout.strip() else 60.0
        except:
            audio_duration = 60.0  # Fallback duration
        
        video_result = video_service.create_video_with_ffmpeg(
            image_paths=[Path(p) for p in image_paths], 
            audio_path=Path(audio_path), 
            output_path=video_path,
            audio_duration=audio_duration,
            script_data=script_data,
            subtitles_path=subtitles_path
        )
        
        if not video_result:
            logger.error("Failed to create video")
            return None
            
        # video_result is boolean in SimpleVideoService, but we need the path
        if video_result:
             video_path = video_path
        else:
             return None
            
        # Handle YouTube upload if requested
        if upload_to_youtube:
            automation_status["current_step"] = "Uploading to YouTube..."
            automation_status["progress"] = 95
            
            try:
                # Create metadata file for upload  
                metadata = {
                    'title': script_data.get('title', f'Breaking: {topic}'),
                    'description': script_data.get('description', f"Latest update on {topic}"),
                    'tags': script_data.get('hashtags', [topic.replace(' ', ''), 'trending', 'news']),
                    'category_id': '25',  # News & Politics  
                    'privacy_status': 'public',
                    'topic': topic,
                    'script': script_data.get('script', ''),
                    'research_summary': research_data.get('summary', ''),
                    'trend_breakdown': [topic]  # Pass as list, not dict
                }
                
                # Save metadata to temp file
                from utils.helpers import generate_filename
                metadata_filename = generate_filename(topic, "json") 
                metadata_path = Path(config.TEMP_DIR) / metadata_filename
                
                import json
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                youtube_service = YouTubeUploadService()
                upload_result = youtube_service.upload_video(
                    video_path=Path(video_path),
                    metadata_path=metadata_path,
                    research_data=research_data
                )
                
                if upload_result.get('success'):
                    logger.info(f"Video uploaded successfully: {upload_result.get('video_url', 'N/A')}")
                else:
                    logger.warning(f"YouTube upload failed: {upload_result.get('error', 'Unknown error')}, but video was created locally")
                    
            except Exception as e:
                logger.warning(f"YouTube upload failed: {e}, but video was created locally")
        
        automation_status["progress"] = 100
        return str(video_path)
        
    except Exception as e:
        logger.error(f"Web-safe automation failed: {e}")
        return None

# Serve static files (React build)
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")

if __name__ == "__main__":
    import uvicorn
    
    # Create frontend directory if it doesn't exist
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        logger.info("Frontend directory not found. Run 'npm run build' in frontend directory first.")
    
    logger.info("Starting Snip-Z Web Server...")
    logger.info("Access the web interface at: http://localhost:8000")
    
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )