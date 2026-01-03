"""
Setup script to configure additional image source API keys
Run this to add Pexels and Unsplash API keys for better image diversity
"""

print("""
╔═══════════════════════════════════════════════════════════════╗
║  Enhanced Image Service - API Key Setup                      ║
╚═══════════════════════════════════════════════════════════════╝

To get the BEST, most diverse images, you should add these FREE API keys:

1. 🎨 PEXELS API (Free - No credit card required)
   - Visit: https://www.pexels.com/api/
   - Click "Get Started"
   - Create free account
   - Copy your API Key

2. 📸 UNSPLASH API (Free - 50 requests/hour)
   - Visit: https://unsplash.com/developers
   - Click "Register as a developer"
   - Create new app
   - Copy your "Access Key"

════════════════════════════════════════════════════════════════

The system will work WITHOUT these keys using just SerpAPI,
but adding them gives you:
✅ More diverse, higher quality images
✅ No watermarks or stock photo logos
✅ Professional photography
✅ Better retention and engagement

════════════════════════════════════════════════════════════════
""")

import os
from pathlib import Path

config_file = Path(__file__).parent / "config.py"

print(f"📝 Your config file: {config_file}\n")
print("To add your keys, either:")
print("  1. Set environment variables:")
print("     export PEXELS_API_KEY='your_key_here'")
print("     export UNSPLASH_ACCESS_KEY='your_key_here'")
print()
print("  2. Or edit config.py directly and replace empty strings")
print()

# Check current status
try:
    import config
    has_pexels = bool(config.PEXELS_API_KEY)
    has_unsplash = bool(config.UNSPLASH_ACCESS_KEY)
    
    print("Current Status:")
    print(f"  Pexels API:   {'✅ Configured' if has_pexels else '❌ Not configured'}")
    print(f"  Unsplash API: {'✅ Configured' if has_unsplash else '❌ Not configured'}")
    print(f"  SerpAPI:      ✅ Configured (primary source)")
    
    if has_pexels and has_unsplash:
        print("\n🎉 All image sources configured! You're getting the best possible images.")
    elif has_pexels or has_unsplash:
        print("\n⚠️  Partial setup - add the missing API key for even better results")
    else:
        print("\n⚠️  Using SerpAPI only - add Pexels/Unsplash for better image diversity")
        
except Exception as e:
    print(f"Error checking config: {e}")

print("\n" + "="*65)
