#!/usr/bin/env python3
"""Generate YouTube OAuth token with upload permissions"""

import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent))
import config

# Scopes required for uploading videos
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube',
    'https://www.googleapis.com/auth/youtube.force-ssl'
]

def generate_token():
    """Generate new YouTube OAuth token with upload permissions"""
    
    print("🎬 YouTube OAuth Token Generator")
    print("=" * 50)
    print()
    print("This will open your browser for YouTube authentication.")
    print("Required permissions:")
    print("  - Upload videos")
    print("  - Manage YouTube account")
    print()
    
    # Create credentials from client secrets
    client_config = {
        "installed": {
            "client_id": config.YOUTUBE_CLIENT_ID,
            "client_secret": config.YOUTUBE_CLIENT_SECRET,
            "redirect_uris": ["http://localhost:8080/", "urn:ietf:wg:oauth:2.0:oob"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
    }
    
    try:
        # Run OAuth flow
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        credentials = flow.run_local_server(port=8080)
        
        # Save credentials
        token_file = Path(__file__).parent / 'youtube_token.pickle'
        with open(token_file, 'wb') as f:
            pickle.dump(credentials, f)
        
        print()
        print("✅ Token generated successfully!")
        print(f"   Saved to: {token_file}")
        print()
        print("🔑 Refresh Token:")
        print(f"   {credentials.refresh_token}")
        print()
        print("📋 Next steps:")
        print("   1. Copy the refresh token above")
        print("   2. Run in Cloud Shell:")
        print(f"      gcloud run services update snip-z --region=europe-west1 \\")
        print(f"        --update-env-vars=\"YOUTUBE_REFRESH_TOKEN={credentials.refresh_token}\"")
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    generate_token()
