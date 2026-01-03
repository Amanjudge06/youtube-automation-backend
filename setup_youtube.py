"""
YouTube API Setup Helper
Interactive script to configure YouTube API credentials
"""

import sys
from pathlib import Path

# Add project root to path  
sys.path.insert(0, str(Path(__file__).parent))

import config

def setup_youtube_credentials():
    """Interactive setup for YouTube API credentials"""
    
    print("🎬 YouTube API Setup Helper")
    print("=" * 50)
    print()
    
    print("This script will help you configure YouTube API credentials.")
    print("You'll need to get these from Google Cloud Console first.")
    print()
    
    print("📋 PREREQUISITES:")
    print("1. Google account")
    print("2. Google Cloud Console access")
    print("3. YouTube Data API v3 enabled")
    print()
    
    # Check current configuration
    current_client_id = config.YOUTUBE_CLIENT_ID
    current_client_secret = config.YOUTUBE_CLIENT_SECRET
    
    print("📊 CURRENT CONFIGURATION:")
    if current_client_id:
        masked_id = current_client_id[:20] + "..." if len(current_client_id) > 20 else current_client_id
        print(f"   Client ID: {masked_id} ✅")
    else:
        print(f"   Client ID: Not configured ❌")
        
    if current_client_secret:
        print(f"   Client Secret: Configured ✅")
    else:
        print(f"   Client Secret: Not configured ❌")
    
    print()
    
    if not current_client_id or not current_client_secret:
        print("🔧 SETUP STEPS:")
        print("-" * 30)
        print()
        
        print("1. 🌐 Go to Google Cloud Console:")
        print("   https://console.cloud.google.com/")
        print()
        
        print("2. 📦 Create or select a project:")
        print("   - Click 'Select a Project' → 'New Project'")
        print("   - Name: 'YouTube Automation' (or any name)")
        print("   - Click 'Create'")
        print()
        
        print("3. 🔌 Enable YouTube Data API v3:")
        print("   - Go to 'APIs & Services' → 'Library'")
        print("   - Search 'YouTube Data API v3'")
        print("   - Click on it and press 'Enable'")
        print()
        
        print("4. 🔑 Create OAuth 2.0 Credentials:")
        print("   - Go to 'APIs & Services' → 'Credentials'") 
        print("   - Click '+ Create Credentials' → 'OAuth client ID'")
        print("   - If needed, configure consent screen (External, basic info)")
        print("   - Application type: 'Desktop application'")
        print("   - Name: 'YouTube Upload Client'")
        print("   - Click 'Create'")
        print()
        
        print("5. 📋 Copy the credentials:")
        print("   - Copy 'Client ID' and 'Client secret'")
        print()
        
        print("6. ⚙️  Configure in this application:")
        print("   Option A - Edit config.py directly:")
        print(f"   YOUTUBE_CLIENT_ID = 'your-client-id-here'")
        print(f"   YOUTUBE_CLIENT_SECRET = 'your-client-secret-here'")
        print()
        print("   Option B - Set environment variables:")
        print(f"   export YOUTUBE_CLIENT_ID='your-client-id'")
        print(f"   export YOUTUBE_CLIENT_SECRET='your-client-secret'")
        print()
        
        print("7. 🧪 Test the configuration:")
        print("   python upload_video.py --test-auth")
        print()
        
        # Option to input credentials interactively
        response = input("Would you like to enter your credentials now? (y/N): ").lower().strip()
        if response == 'y':
            setup_credentials_interactive()
    else:
        print("✅ YouTube credentials are already configured!")
        print()
        test_response = input("Would you like to test the authentication? (y/N): ").lower().strip()
        if test_response == 'y':
            test_authentication()


def setup_credentials_interactive():
    """Interactive credential input"""
    
    print()
    print("🔐 Interactive Credential Setup:")
    print("-" * 35)
    
    client_id = input("Enter YouTube Client ID: ").strip()
    client_secret = input("Enter YouTube Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("❌ Invalid input. Please try again.")
        return
    
    # Update config file
    config_path = Path(__file__).parent / "config.py"
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Replace the credential lines
        import re
        
        # Replace Client ID
        content = re.sub(
            r'YOUTUBE_CLIENT_ID = os\.getenv\("YOUTUBE_CLIENT_ID", "[^"]*"\)',
            f'YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "{client_id}")',
            content
        )
        
        # Replace Client Secret
        content = re.sub(
            r'YOUTUBE_CLIENT_SECRET = os\.getenv\("YOUTUBE_CLIENT_SECRET", "[^"]*"\)',
            f'YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "{client_secret}")',
            content
        )
        
        # Write back to file
        with open(config_path, 'w') as f:
            f.write(content)
        
        print("✅ Credentials saved to config.py!")
        print()
        
        # Test authentication
        test_response = input("Would you like to test the authentication now? (y/N): ").lower().strip()
        if test_response == 'y':
            test_authentication()
    
    except Exception as e:
        print(f"❌ Error saving credentials: {e}")
        print("Please edit config.py manually.")


def test_authentication():
    """Test YouTube API authentication"""
    
    print()
    print("🧪 Testing YouTube authentication...")
    
    import subprocess
    import os
    
    # Run the authentication test
    script_dir = Path(__file__).parent
    python_path = script_dir / ".venv" / "bin" / "python"
    
    try:
        result = subprocess.run([
            str(python_path), 
            "upload_video.py", 
            "--test-auth"
        ], capture_output=True, text=True, cwd=script_dir)
        
        if result.returncode == 0:
            print("✅ Authentication test passed!")
            print()
            print("🚀 You're ready to upload videos!")
            print("   python upload_video.py (upload latest video)")
            print("   python main.py --upload (generate + upload)")
        else:
            print("❌ Authentication test failed.")
            print("Error output:")
            print(result.stderr)
    
    except Exception as e:
        print(f"❌ Error running test: {e}")


if __name__ == "__main__":
    setup_youtube_credentials()