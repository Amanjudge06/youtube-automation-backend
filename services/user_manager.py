"""
User Management System for YouTube Automation SaaS
Handles multiple users and their YouTube channel connections
"""

import json
import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class UserManager:
    """Manages user accounts and their YouTube channel connections"""
    
    def __init__(self, data_dir: str = "user_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.users_file = self.data_dir / "users.json"
        self.users = self._load_users()
    
    def _load_users(self) -> Dict:
        """Load users database"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading users: {e}")
        return {}
    
    def _save_users(self):
        """Save users database"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def create_user(self, user_id: str, email: str = None) -> Dict:
        """Create a new user account"""
        if user_id in self.users:
            return self.users[user_id]
        
        user_data = {
            "user_id": user_id,
            "email": email,
            "created_at": str(datetime.now()),
            "youtube_channels": [],
            "active_channel": None,
            "settings": {
                "voice_id": "default",
                "language": "en",
                "video_privacy": "public"
            }
        }
        
        self.users[user_id] = user_data
        self._save_users()
        
        # Create user-specific directories
        user_dir = self.data_dir / user_id
        user_dir.mkdir(exist_ok=True)
        (user_dir / "tokens").mkdir(exist_ok=True)
        (user_dir / "uploads").mkdir(exist_ok=True)
        
        logger.info(f"Created new user: {user_id}")
        return user_data
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """Get user data"""
        return self.users.get(user_id)
    
    def add_youtube_channel(self, user_id: str, channel_data: Dict, credentials) -> bool:
        """Add YouTube channel to user account"""
        try:
            if user_id not in self.users:
                self.create_user(user_id)
            
            # Save user-specific YouTube credentials
            token_file = self.data_dir / user_id / "tokens" / f"youtube_{channel_data['id']}.pickle"
            with open(token_file, 'wb') as f:
                pickle.dump(credentials, f)
            
            # Add channel to user's channel list
            channel_info = {
                "id": channel_data["id"],
                "title": channel_data["title"],
                "subscriber_count": channel_data.get("subscriber_count", 0),
                "added_at": str(datetime.now()),
                "token_file": str(token_file)
            }
            
            # Check if channel already exists
            existing_channels = self.users[user_id]["youtube_channels"]
            channel_exists = any(ch["id"] == channel_data["id"] for ch in existing_channels)
            
            if not channel_exists:
                self.users[user_id]["youtube_channels"].append(channel_info)
            
            # Set as active channel if it's the first one
            if not self.users[user_id]["active_channel"]:
                self.users[user_id]["active_channel"] = channel_data["id"]
            
            self._save_users()
            logger.info(f"Added YouTube channel {channel_data['title']} to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding YouTube channel: {e}")
            return False
    
    def get_user_channels(self, user_id: str) -> List[Dict]:
        """Get user's YouTube channels"""
        user = self.get_user(user_id)
        if user:
            return user.get("youtube_channels", [])
        return []
    
    def set_active_channel(self, user_id: str, channel_id: str) -> bool:
        """Set user's active YouTube channel"""
        try:
            if user_id in self.users:
                # Verify channel belongs to user
                user_channels = self.get_user_channels(user_id)
                if any(ch["id"] == channel_id for ch in user_channels):
                    self.users[user_id]["active_channel"] = channel_id
                    self._save_users()
                    return True
            return False
        except Exception as e:
            logger.error(f"Error setting active channel: {e}")
            return False
    
    def get_user_youtube_credentials(self, user_id: str, channel_id: str = None):
        """Get YouTube credentials for user's channel"""
        try:
            if not channel_id:
                user = self.get_user(user_id)
                if user:
                    channel_id = user.get("active_channel")
            
            if not channel_id:
                return None
            
            token_file = self.data_dir / user_id / "tokens" / f"youtube_{channel_id}.pickle"
            if token_file.exists():
                with open(token_file, 'rb') as f:
                    return pickle.load(f)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user credentials: {e}")
            return None


# Global user manager instance
user_manager = UserManager()