import os
from supabase import create_client, Client
import logging
import config
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class SupabaseService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SupabaseService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.url = config.SUPABASE_URL
        self.key = config.SUPABASE_KEY
        self.client: Optional[Client] = None
        
        if self.url and self.key:
            try:
                self.client = create_client(self.url, self.key)
                logger.info("✅ Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Supabase client: {e}")
        else:
            logger.warning("⚠️ Supabase credentials not found in config")
            
        self._initialized = True

    def is_available(self) -> bool:
        return self.client is not None

    # Authentication Methods
    def sign_up(self, email: str, password: str) -> Dict:
        if not self.is_available():
            return {"error": "Supabase not configured"}
        try:
            res = self.client.auth.sign_up({
                "email": email,
                "password": password
            })
            return res
        except Exception as e:
            logger.error(f"Sign up error: {e}")
            return {"error": str(e)}

    def sign_in(self, email: str, password: str) -> Dict:
        if not self.is_available():
            return {"error": "Supabase not configured"}
        try:
            res = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            return res
        except Exception as e:
            logger.error(f"Sign in error: {e}")
            return {"error": str(e)}

    def sign_out(self) -> Dict:
        if not self.is_available():
            return {"error": "Supabase not configured"}
        try:
            res = self.client.auth.sign_out()
            return res
        except Exception as e:
            logger.error(f"Sign out error: {e}")
            return {"error": str(e)}

    # User Profile Methods
    def get_user_profile(self, user_id: str) -> Dict:
        """Get user profile information"""
        if not self.is_available():
            return {}
        try:
            response = self.client.table('user_profiles').select("*").eq('user_id', user_id).single().execute()
            if response.data:
                return response.data
            return {}
        except Exception as e:
            logger.error(f"Error fetching profile: {e}")
            return {}
    
    def update_user_profile(self, user_id: str, profile_data: Dict) -> bool:
        """Update user profile"""
        if not self.is_available():
            return False
        try:
            self.client.table('user_profiles').upsert({
                "user_id": user_id,
                **profile_data
            }, on_conflict="user_id").execute()
            return True
        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            return False

    # User Settings Methods
    def get_user_settings(self, user_id: str) -> Dict:
        """Get user API keys and settings"""
        if not self.is_available():
            return {}
        try:
            response = self.client.table('user_settings').select("*").eq('user_id', user_id).single().execute()
            if response.data:
                return response.data
            return {}
        except Exception as e:
            logger.error(f"Error fetching user settings: {e}")
            return {}
    
    def update_user_settings(self, user_id: str, settings: Dict) -> bool:
        """Update user settings and API keys"""
        if not self.is_available():
            return False
        try:
            self.client.table('user_settings').upsert({
                "user_id": user_id,
                **settings
            }, on_conflict="user_id").execute()
            return True
        except Exception as e:
            logger.error(f"Error updating user settings: {e}")
            return False

    # Video History Methods
    def save_video_metadata(self, user_id: str, video_data: Dict) -> Dict:
        """Save video generation to history"""
        if not self.is_available():
            return {}
        try:
            data = {
                "user_id": user_id,
                **video_data
            }
            response = self.client.table('video_history').insert(data).execute()
            return response.data[0] if response.data else {}
        except Exception as e:
            logger.error(f"Error saving video metadata: {e}")
            return {"error": str(e)}
    
    def get_video_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's video generation history"""
        if not self.is_available():
            return []
        try:
            response = self.client.table('video_history') \
                .select("*") \
                .eq('user_id', user_id) \
                .order('created_at', desc=True) \
                .limit(limit) \
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Error fetching video history: {e}")
            return []
    
    def update_video_analytics(self, video_id: str, analytics: Dict) -> bool:
        """Update video analytics (views, likes, etc)"""
        if not self.is_available():
            return False
        try:
            self.client.table('video_history').update(analytics).eq('id', video_id).execute()
            return True
        except Exception as e:
            logger.error(f"Error updating video analytics: {e}")
            return False

    # Usage Tracking Methods
    def get_user_usage(self, user_id: str) -> Dict:
        """Get user's current usage stats and limits"""
        if not self.is_available():
            return {
                "videos_generated_today": 0,
                "videos_generated_month": 0,
                "max_videos_per_day": 3,
                "max_videos_per_month": 30,
                "plan_type": "free"
            }
        try:
            response = self.client.table('user_usage').select("*").eq('user_id', user_id).single().execute()
            if response.data:
                return response.data
            return {
                "videos_generated_today": 0,
                "videos_generated_month": 0,
                "max_videos_per_day": 3,
                "max_videos_per_month": 30,
                "plan_type": "free"
            }
        except Exception as e:
            logger.error(f"Error fetching user usage: {e}")
            return {
                "videos_generated_today": 0,
                "videos_generated_month": 0,
                "max_videos_per_day": 3,
                "max_videos_per_month": 30,
                "plan_type": "free"
            }
    
    def check_usage_limit(self, user_id: str) -> Dict[str, Any]:
        """Check if user can generate another video"""
        usage = self.get_user_usage(user_id)
        daily_remaining = usage.get('max_videos_per_day', 3) - usage.get('videos_generated_today', 0)
        monthly_remaining = usage.get('max_videos_per_month', 30) - usage.get('videos_generated_month', 0)
        
        can_generate = daily_remaining > 0 and monthly_remaining > 0
        
        return {
            "allowed": can_generate,
            "daily_remaining": daily_remaining,
            "monthly_remaining": monthly_remaining,
            "plan_type": usage.get('plan_type', 'free')
        }
    
    def increment_usage(self, user_id: str) -> bool:
        """Increment usage counter after successful video generation"""
        if not self.is_available():
            return False
        try:
            # Call the database function
            self.client.rpc('increment_usage', {'p_user_id': user_id}).execute()
            return True
        except Exception as e:
            logger.error(f"Error incrementing usage: {e}")
            return False

    # Automation Status Methods
    def get_automation_status(self, user_id: str) -> Dict[str, Any]:
        """Get current automation status from Supabase"""
        # Safety check for legacy demo_user to prevent DB crashes
        if user_id == "demo_user":
            return {
                "running": False,
                "current_step": "Demo Mode (Legacy)",
                "progress": 0,
                "logs": [],
                "error": "Please log in to use automation",
                "video_path": None,
                "youtube_url": None,
                "last_run": None
            }
            
        if not self.is_available():
            return {
                "running": False,
                "current_step": "",
                "progress": 0,
                "logs": [],
                "error": None,
                "video_path": None,
                "youtube_url": None,
                "last_run": None
            }
        try:
            response = self.client.table('automation_status').select('*').eq('user_id', user_id).single().execute()
            if response.data:
                data = response.data
                return {
                    "running": data.get("running", False),
                    "current_step": data.get("current_step", ""),
                    "progress": data.get("progress", 0),
                    "logs": data.get("logs", []),
                    "error": data.get("error"),
                    "video_path": data.get("video_path"),
                    "youtube_url": data.get("youtube_url"),
                    "last_run": data.get("last_run")
                }
        except Exception as e:
            logger.error(f"Error getting automation status: {e}")
        
        # Return default status if error or not found
        return {
            "running": False,
            "current_step": "",
            "progress": 0,
            "logs": [],
            "error": None,
            "video_path": None,
            "youtube_url": None,
            "last_run": None
        }
    
    def update_automation_status(self, user_id: str, status: Dict[str, Any]) -> bool:
        """Update automation status in Supabase"""
        if not self.is_available():
            return False
        try:
            # Upsert the status
            self.client.table('automation_status').upsert({
                "user_id": user_id,
                "running": status.get("running", False),
                "current_step": status.get("current_step", ""),
                "progress": status.get("progress", 0),
                "logs": status.get("logs", []),
                "error": status.get("error"),
                "video_path": status.get("video_path"),
                "youtube_url": status.get("youtube_url"),
                "last_run": status.get("last_run"),
                "updated_at": "now()"
            }, on_conflict="user_id").execute()
            return True
        except Exception as e:
            logger.error(f"Error updating automation status: {e}")
            return False

    # Storage Methods
    def upload_file(self, bucket: str, path: str, file_path: Path) -> str:
        if not self.is_available():
            return ""
        try:
            with open(file_path, 'rb') as f:
                self.client.storage.from_(bucket).upload(path, f)
            
            # Get public URL
            public_url = self.client.storage.from_(bucket).get_public_url(path)
            return public_url
        except Exception as e:
            logger.error(f"Error uploading file to Supabase: {e}")
            return ""    
    # Schedule Methods (with user isolation)
    def get_schedules(self, user_id: str) -> List[Dict]:
        """Get all schedules for a specific user"""
        if not self.is_available():
            return []
        try:
            response = self.client.table('schedules') \
                .select("*") \
                .eq('user_id', user_id) \
                .execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching schedules for user {user_id}: {e}")
            return []
    
    def save_schedule(self, user_id: str, schedule_data: Dict) -> bool:
        """Save a new schedule for a user"""
        if not self.is_available():
            return False
        try:
            data = {
                "user_id": user_id,
                **schedule_data
            }
            self.client.table('schedules').insert(data).execute()
            return True
        except Exception as e:
            logger.error(f"Error saving schedule: {e}")
            return False
    
    def update_schedule(self, schedule_id: str, user_id: str, schedule_data: Dict) -> bool:
        """Update an existing schedule (with user verification)"""
        if not self.is_available():
            return False
        try:
            self.client.table('schedules') \
                .update(schedule_data) \
                .eq('id', schedule_id) \
                .eq('user_id', user_id) \
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error updating schedule: {e}")
            return False
    
    def delete_schedule(self, schedule_id: str, user_id: str) -> bool:
        """Delete a schedule (with user verification)"""
        if not self.is_available():
            return False
        try:
            self.client.table('schedules') \
                .delete() \
                .eq('id', schedule_id) \
                .eq('user_id', user_id) \
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error deleting schedule: {e}")
            return False
    
    def get_all_active_schedules(self) -> List[Dict]:
        """Get all active schedules from all users (for scheduler service)"""
        if not self.is_available():
            return []
        try:
            response = self.client.table('schedules') \
                .select("*") \
                .eq('is_active', True) \
                .execute()
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching all active schedules: {e}")
            return []