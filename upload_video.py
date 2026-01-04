"""
Upload Script for Generated YouTube Videos
Handles the upload process with SEO optimization
"""

import logging
import sys
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from services.youtube_upload_service import YouTubeUploadService
from services.research_service import ResearchService
from services.supabase_service import SupabaseService
from utils.helpers import setup_logging
import config

setup_logging()
logger = logging.getLogger(__name__)


def upload_latest_video():
    """Upload the latest generated video to YouTube"""
    
    logger.info("=" * 70)
    logger.info("YOUTUBE VIDEO UPLOAD - STARTING")
    logger.info("=" * 70)
    
    try:
        # Find the latest video file
        output_dir = Path(config.OUTPUT_DIR)
        video_files = list(output_dir.glob("*.mp4"))
        
        if not video_files:
            logger.error("No video files found in output directory")
            return False
        
        # Get the latest video file
        latest_video = max(video_files, key=lambda p: p.stat().st_mtime)
        
        # Find corresponding metadata file
        metadata_file = latest_video.with_suffix('.json')
        if not metadata_file.exists():
            logger.error(f"Metadata file not found: {metadata_file}")
            return False
        
        logger.info(f"📽️  Video to upload: {latest_video.name}")
        logger.info(f"📄 Metadata file: {metadata_file.name}")
        
        # Load metadata to get topic for research enhancement
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        topic = metadata.get('topic', '')
        logger.info(f"🎯 Topic: {topic}")
        
        # Get enhanced research data for better SEO
        logger.info("📊 Fetching enhanced research data for SEO optimization...")
        research_service = ResearchService()
        research_data = None
        
        try:
            # Create a basic breakdown for research enhancement
            basic_breakdown = {
                "topic_category": "general",
                "trend_timing": "upload_optimization",
                "volume_tier": "high",
                "research_angles": [
                    f"Latest developments about {topic}",
                    f"Why {topic} is important",
                    f"Key facts about {topic}"
                ]
            }
            research_data = research_service.research_trending_topic(topic, basic_breakdown)
            
            if research_data and not research_data.get("fallback"):
                logger.info("✅ Enhanced research data obtained for SEO")
            else:
                logger.info("⚠️  Using basic metadata (research enhancement unavailable)")
                
        except Exception as e:
            logger.warning(f"Could not fetch research enhancement: {e}")
        
        # Initialize upload service
        logger.info("🚀 Initializing YouTube upload service...")
        upload_service = YouTubeUploadService()
        
        # Upload video
        logger.info("📤 Starting video upload to YouTube...")
        result = upload_service.upload_video(latest_video, metadata_file, research_data)
        
        if result.get('success'):
            video_id = result['video_id']
            video_url = result['video_url']
            
            print("\n" + "🎉" * 50)
            print("SUCCESS! VIDEO UPLOADED TO YOUTUBE")
            print("🎉" * 50)
            print(f"\n📺 Video ID: {video_id}")
            print(f"🔗 Video URL: {video_url}")
            print(f"🎬 Title: {result['metadata']['optimized_title']}")
            print(f"🏷️  Tags: {', '.join(result['metadata']['tags'])}")
            print(f"#️⃣  Hashtags: {' '.join(result['metadata']['hashtags'])}")
            print(f"🔒 Privacy: {result['metadata']['privacy_status']}")
            
            print(f"\n📄 Description Preview:")
            description = result['metadata']['optimized_description']
            print(description[:200] + "..." if len(description) > 200 else description)
            
            print(f"\n📊 Upload completed at: {result['metadata']['upload_timestamp']}")
            print("\n🚀 Your video is now live on YouTube!")
            
            logger.info("✅ Video upload completed successfully")
            
            # Sync with Supabase
            logger.info("Syncing with Supabase...")
            try:
                supabase_service = SupabaseService()
                if supabase_service.is_available():
                    user_id = "e3bdcc94-2efa-479f-9138-44c33790b2d3"
                    storage_path = f"{user_id}/{latest_video.name}"
                    
                    # Upload file
                    public_url = supabase_service.upload_file("videos", storage_path, latest_video)
                    
                    if public_url:
                        video_data = {
                            "title": result['metadata']['optimized_title'],
                            "description": result['metadata']['optimized_description'],
                            "topic": topic,
                            "file_path": str(latest_video),
                            "storage_path": storage_path,
                            "status": "completed",
                            "youtube_url": video_url
                        }
                        supabase_service.save_video_metadata(user_id, video_data)
                        logger.info("✅ Synced with Supabase")
                    else:
                        logger.warning("⚠️ Failed to upload to Supabase storage")
            except Exception as e:
                logger.error(f"Supabase sync failed: {e}")

            return True
        else:
            error = result.get('error', 'Unknown error')
            logger.error(f"❌ Upload failed: {error}")
            print(f"\n❌ Upload failed: {error}")
            
            # Provide helpful error guidance
            if "authentication" in error.lower() or "credentials" in error.lower():
                print("\n🔧 SETUP REQUIRED:")
                print("1. Go to https://console.cloud.google.com/")
                print("2. Create a new project or select existing")
                print("3. Enable YouTube Data API v3")
                print("4. Create OAuth 2.0 credentials (Desktop application)")
                print("5. Add your Client ID and Secret to config.py:")
                print(f"   YOUTUBE_CLIENT_ID = 'your-client-id'")
                print(f"   YOUTUBE_CLIENT_SECRET = 'your-client-secret'")
                
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}", exc_info=True)
        print(f"\n❌ Unexpected error: {e}")
        return False


def upload_specific_video(video_path: str):
    """Upload a specific video file"""
    
    video_file = Path(video_path)
    if not video_file.exists():
        logger.error(f"Video file not found: {video_path}")
        return False
    
    metadata_file = video_file.with_suffix('.json')
    if not metadata_file.exists():
        logger.error(f"Metadata file not found: {metadata_file}")
        return False
    
    logger.info(f"Uploading specific video: {video_file}")
    
    # Load metadata
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    # Initialize upload service
    upload_service = YouTubeUploadService()
    
    # Upload video
    result = upload_service.upload_video(video_file, metadata_file)
    
    if result.get('success'):
        logger.info("✅ Specific video upload completed successfully")
        print(f"\n✅ Video uploaded: {result['video_url']}")
        return True
    else:
        logger.error(f"❌ Upload failed: {result.get('error', 'Unknown error')}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Upload YouTube Shorts videos")
    parser.add_argument(
        "--video",
        type=str,
        help="Path to specific video file (if not provided, uploads latest)"
    )
    parser.add_argument(
        "--test-auth",
        action="store_true",
        help="Test YouTube authentication only"
    )
    
    args = parser.parse_args()
    
    if args.test_auth:
        print("Testing YouTube authentication...")
        upload_service = YouTubeUploadService()
        if upload_service.authenticate():
            print("✅ YouTube authentication successful!")
        else:
            print("❌ YouTube authentication failed!")
            print("\nPlease configure your YouTube API credentials:")
            print("1. Set YOUTUBE_CLIENT_ID in config.py")
            print("2. Set YOUTUBE_CLIENT_SECRET in config.py")
        sys.exit(0)
    
    if args.video:
        success = upload_specific_video(args.video)
    else:
        success = upload_latest_video()
    
    sys.exit(0 if success else 1)