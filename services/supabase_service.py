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

    # Database Methods
    def get_user_profile(self, user_id: str) -> Dict:
        if not self.is_available():
            return {}
        try:
            response = self.client.table('profiles').select("*").eq('id', user_id).execute()
            if response.data:
                return response.data[0]
            return {}
        except Exception as e:
            logger.error(f"Error fetching profile: {e}")
            return {}

    def save_video_metadata(self, user_id: str, video_data: Dict) -> Dict:
        if not self.is_available():
            return {}
        try:
            data = {
                "user_id": user_id,
                **video_data
            }
            response = self.client.table('videos').insert(data).execute()
            return response.data
        except Exception as e:
            logger.error(f"Error saving video metadata: {e}")
            return {"error": str(e)}

    # Automation Status Methods
    def get_automation_status(self, user_id: str = "demo_user") -> Dict[str, Any]:
        """Get current automation status from Supabase"""
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
