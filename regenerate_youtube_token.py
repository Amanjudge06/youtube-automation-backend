"""
Script to regenerate YouTube refresh token with correct scopes
This will give you a refresh token that works with Cloud Run
"""

import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
import os
from pathlib import Path

# Required scopes for YouTube upload and channel management
SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube.readonly',
    'https://www.googleapis.com/auth/youtube.force-ssl'  # Full access scope
]

def get_client_config():
    """Load client credentials from file or environment"""
    creds_file = Path("youtube_credentials.json")
    
    if creds_file.exists():
        with open(creds_file, 'r') as f:
            return json.load(f)
    
    # Fallback to environment variables
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        raise Exception("YouTube credentials not found. Set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET")
    
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080/", "urn:ietf:wg:oauth:2.0:oob"]
        }
    }

def main():
    print("=" * 70)
    print("YouTube Refresh Token Generator")
    print("=" * 70)
    print()
    
    # Load client config
    try:
        client_config = get_client_config()
    except Exception as e:
        print(f"❌ Error loading credentials: {e}")
        return
    
    print("✅ Loaded OAuth credentials")
    print()
    print("🔐 Requesting these scopes:")
    for scope in SCOPES:
        print(f"   • {scope}")
    print()
    
    # Create OAuth flow
    flow = InstalledAppFlow.from_client_config(
        client_config,
        scopes=SCOPES
    )
    
    # Run local server to get authorization
    print("🌐 Starting local authentication server...")
    print("📱 Your browser will open for Google authentication")
    print()
    
    try:
        creds = flow.run_local_server(
            port=8080,
            access_type='offline',
            prompt='consent'  # Force consent screen to get refresh token
        )
        
        print()
        print("=" * 70)
        print("✅ Authentication successful!")
        print("=" * 70)
        print()
        
        if creds.refresh_token:
            print("🎉 Got refresh token!")
            print()
            print("📋 Add this to your Cloud Run environment variables:")
            print()
            print("YOUTUBE_REFRESH_TOKEN=" + creds.refresh_token)
            print()
            print("=" * 70)
            print()
            print("📝 To set this in Cloud Run:")
            print()
            print("gcloud run services update snip-z \\")
            print("  --region europe-west1 \\")
            print(f"  --update-env-vars YOUTUBE_REFRESH_TOKEN={creds.refresh_token}")
            print()
            
            # Save to local .env file
            env_file = Path(".env")
            if env_file.exists():
                with open(env_file, 'r') as f:
                    lines = f.readlines()
                
                # Update or add YOUTUBE_REFRESH_TOKEN
                updated = False
                for i, line in enumerate(lines):
                    if line.startswith("YOUTUBE_REFRESH_TOKEN="):
                        lines[i] = f"YOUTUBE_REFRESH_TOKEN={creds.refresh_token}\n"
                        updated = True
                        break
                
                if not updated:
                    lines.append(f"YOUTUBE_REFRESH_TOKEN={creds.refresh_token}\n")
                
                with open(env_file, 'w') as f:
                    f.writelines(lines)
                
                print("✅ Updated .env file with new refresh token")
                print()
            
            # Test the credentials
            print("🧪 Testing credentials...")
            from googleapiclient.discovery import build
            
            youtube = build('youtube', 'v3', credentials=creds)
            request = youtube.channels().list(part='snippet', mine=True)
            response = request.execute()
            
            if response.get('items'):
                channel = response['items'][0]['snippet']
                print(f"✅ Connected to channel: {channel['title']}")
                print()
            
        else:
            print("❌ No refresh token received. Make sure to:")
            print("   1. Use 'consent' prompt")
            print("   2. Set access_type to 'offline'")
            print()
    
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        print()
        print("💡 Make sure:")
        print("   • You're using the correct Google account")
        print("   • The OAuth app is approved")
        print("   • http://localhost:8080/ is in authorized redirect URIs")

if __name__ == "__main__":
    main()
